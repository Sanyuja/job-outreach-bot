#!/usr/bin/env python
"""
Build a list of (job, contact) pairs from raw_jobs.csv.

- Reads a "raw jobs" CSV (typically exported from Google Sheets via export_sheet_to_csv.py)
- Infers company_domain from company_url or job_url if missing
- Filters out obviously irrelevant roles using job_profile_rules.is_title_relevant(...)
- Uses contact_enricher.enrich_contacts(...) to fetch contacts for each company/domain
- Writes an output CSV with one row per (job, contact) ready for batch_apply.py
"""

import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Any

from src.contact_enricher import enrich_contacts  # your existing Hunter + fallback logic
from src.job_profile_rules import is_title_relevant  # your existing relevance rules


def infer_company_domain(
    company_domain: str | None,
    company_url: str | None,
    job_url: str | None,
) -> str:
    """
    Try to derive a clean company domain.

    Priority:
      1) Explicit company_domain if present (normalize)
      2) Host from company_url
      3) Host from job_url, but skip known ATS hosts (greenhouse.io, lever.co, ashbyhq.com)

    Returns e.g. 'bluerose.ai' or '' if we can't infer.
    """

    # 1) If already present, normalize and use it
    if company_domain:
        d = company_domain.strip().lower()
        # Remove protocol
        d = re.sub(r"^https?://", "", d)
        # Strip leading 'www.'
        if d.startswith("www."):
            d = d[4:]
        # Drop any path
        d = d.split("/")[0]
        return d

    def host_from_url(url: str | None) -> str | None:
        if not url:
            return None
        u = url.strip()
        # Handle bare domains like "bluerose.ai"
        if not u.startswith("http://") and not u.startswith("https://"):
            u = "https://" + u
        parsed = urlparse(u)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host or None

    # 2) Try company_url
    host = host_from_url(company_url)
    if host:
        return host

    # 3) Try job_url, but skip ATS hosts
    host = host_from_url(job_url)
    if host and not any(ats in host for ats in ["greenhouse.io", "lever.co", "ashbyhq.com"]):
        return host

    return ""


def build_job_list(raw_csv: Path, output_csv: Path) -> None:
    print(f"[INFO] Building job list from {raw_csv} \u2192 {output_csv}")

    if not raw_csv.exists():
        raise FileNotFoundError(f"Raw jobs CSV not found: {raw_csv}")

    rows: List[Dict[str, Any]] = []
    with raw_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip completely empty lines
            if not any(v.strip() for v in row.values() if isinstance(v, str)):
                continue
            rows.append(row)

    print(f"[INFO] Loaded {len(rows)} raw jobs from {raw_csv}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    contact_rows: List[Dict[str, Any]] = []

    for idx, raw in enumerate(rows, start=1):
        title = (raw.get("job_title") or "").strip()
        job_url = (raw.get("job_url") or "").strip()
        company = (raw.get("company") or "").strip()
        company_url = (raw.get("company_url") or "").strip()
        company_domain_raw = (raw.get("company_domain") or "").strip()
        location = (raw.get("location") or "").strip()
        job_id = (raw.get("job_id") or "").strip()

        # Infer the domain in a robust way
        company_domain = infer_company_domain(company_domain_raw, company_url, job_url)

        # Basic sanity check
        if not title or not job_url or not company:
            print(f"[SKIP] Missing basic fields in row: {raw}")
            continue

        print(f"\n[JOB] {idx}: '{title}' @ {company}")

        # Filter by title relevance using your existing rules
        if not is_title_relevant(title):
            print(f"[FILTER] Skipping non-relevant title: '{title}' @ {company}")
            continue

        # Enrich contacts for this company/domain (Hunter + fallbacks handled inside)
        contacts = enrich_contacts(company, company_domain)
        if not contacts:
            print(f"[INFO] No contacts found for {company}, skipping this job.")
            continue

        # Build one output row per contact
        for contact in contacts:
            contact_email = (contact.get("email") or contact.get("value") or "").strip()
            if not contact_email:
                continue

            contact_name = (
                f"{(contact.get('first_name') or '').strip()} {(contact.get('last_name') or '').strip()}"
            ).strip()
            contact_role = (contact.get("position") or "").strip()

            contact_rows.append(
                {
                    "job_id": job_id,
                    "job_title": title,
                    "job_url": job_url,
                    "company": company,
                    "company_domain": company_domain,
                    "company_url": company_url,
                    "location": location,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_role": contact_role,
                    "source": contact.get("source") or "hunter",
                }
            )

    # Write the output CSV
    if contact_rows:
        fieldnames = [
            "job_id",
            "job_title",
            "job_url",
            "company",
            "company_domain",
            "company_url",
            "location",
            "contact_name",
            "contact_email",
            "contact_role",
            "source",
        ]
        with output_csv.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(contact_rows)
        print(f"\n[RESULT] Wrote {len(contact_rows)} contact rows to {output_csv}")
    else:
        # If no contacts matched, still create an empty file with header so batch_apply.py
        # can run without exploding.
        fieldnames = [
            "job_id",
            "job_title",
            "job_url",
            "company",
            "company_domain",
            "company_url",
            "location",
            "contact_name",
            "contact_email",
            "contact_role",
            "source",
        ]
        with output_csv.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
        print(f"\n[RESULT] Wrote 0 contact rows to {output_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build job-contact list from raw jobs CSV.")
    parser.add_argument(
        "--raw_csv",
        type=str,
        default="jobs/raw_jobs.csv",
        help="Path to the raw jobs CSV (exported from Google Sheets).",
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default="jobs/jobs_batch.csv",
        help="Path to the output CSV with one row per (job, contact).",
    )
    args = parser.parse_args()

    raw_path = Path(args.raw_csv)
    out_path = Path(args.output_csv)

    build_job_list(raw_path, out_path)


if __name__ == "__main__":
    main()
