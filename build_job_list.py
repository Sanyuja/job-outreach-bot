# build_job_list.py

# build_job_list.py

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # <-- add this

from src.job_profile_rules import is_relevant_title, guess_use_jd
from src.contact_enricher import find_contacts_for_company



def build_job_list(raw_csv_path: str, output_csv_path: str):
    raw_path = Path(raw_csv_path)
    if not raw_path.exists():
        print(f"[ERROR] Raw jobs CSV not found: {raw_path}")
        sys.exit(1)

    out_path = Path(output_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    if not raw_rows:
        print(f"[INFO] No rows in raw jobs CSV: {raw_path}")
        return

    print(f"[INFO] Loaded {len(raw_rows)} raw jobs from {raw_path}")

    fieldnames = [
        "job_id",
        "job_title",
        "job_url",
        "company",
        "company_url",
        "contact_name",
        "contact_email",
        "contact_title",
        "use_jd",
    ]

    job_id_counter = 0
    written_rows = 0

    with out_path.open("w", encoding="utf-8", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for raw in raw_rows:
            title = raw.get("job_title", "").strip()
            job_url = raw.get("job_url", "").strip()
            company = raw.get("company", "").strip()
            company_url = raw.get("company_url", "").strip()
            company_domain = raw.get("company_domain", "").strip()

            if not title or not job_url or not company:
                print(f"[SKIP] Missing basic fields in row: {raw}")
                continue

            if not is_relevant_title(title):
                print(f"[FILTER] Skipping non-relevant title: '{title}' @ {company}")
                continue

            job_id_counter += 1
            job_id = job_id_counter
            use_jd = guess_use_jd(job_url)

            print(f"\n[JOB] {job_id}: '{title}' @ {company}")
            contacts = find_contacts_for_company(
                company_name=company,
                company_url=company_url or None,
                company_domain=company_domain or None,
                max_contacts=5,
            )

            if not contacts:
                print(f"[INFO] No contacts found for {company}, skipping this job.")
                continue

            for c in contacts:
                writer.writerow(
                    {
                        "job_id": job_id,
                        "job_title": title,
                        "job_url": job_url,
                        "company": company,
                        "company_url": company_url,
                        "contact_name": c.get("name") or "",
                        "contact_email": c.get("email") or "",
                        "contact_title": c.get("position") or "",
                        "use_jd": use_jd,
                    }
                )
                written_rows += 1

    print(f"\n[RESULT] Wrote {written_rows} contact rows to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build jobs_batch.csv from raw_jobs.csv")
    parser.add_argument("--raw_csv", required=True, help="Path to raw jobs CSV")
    parser.add_argument("--output_csv", required=True, help="Path to output jobs batch CSV")
    args = parser.parse_args()

    print(f"[INFO] Building job list from {args.raw_csv} → {args.output_csv}")
    build_job_list(args.raw_csv, args.output_csv)
