# batch_apply.py

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.email_generator import draft_email
from src.gmail_draft import create_draft_with_resume
from src.scraper import fetch_job_description

load_dotenv()


def process_row(row, resume_path: str):
    job_id = row.get("job_id", "").strip()
    job_title = row.get("job_title", "").strip()
    job_url = row.get("job_url", "").strip()
    company = row.get("company", "").strip()
    company_url = row.get("company_url", "").strip()
    contact_name = row.get("contact_name", "").strip()
    contact_email = row.get("contact_email", "").strip()
    contact_title = row.get("contact_title", "").strip()
    use_jd_flag = (row.get("use_jd", "") or "").strip().lower()

    missing = [
        name
        for name, val in [
            ("job_title", job_title),
            ("job_url", job_url),
            ("company", company),
            ("contact_name", contact_name),
            ("contact_email", contact_email),
        ]
        if not val
    ]

    if missing:
        print(f"[SKIP] Row missing required fields {missing}: {row}")
        return

    print(f"\n[ROW] job_id={job_id or '?'} '{job_title}' @ {company} → {contact_name} <{contact_email}>")

    # Decide whether to scrape JD
    job_description = ""
    if use_jd_flag in ("yes", "y", "true", "1"):
        print(f"[JD] Fetching job description from {job_url}")
        job_description = fetch_job_description(job_url)
        if not job_description:
            print("[JD] Warning: empty JD, continuing with background-only context.")
    else:
        print(f"[JD] Skipping JD scrape for {job_url} (use_jd={use_jd_flag})")

    # Generate email HTML using your personalized generator
    email_html = draft_email(
        job_title=job_title,
        job_url=job_url,
        hiring_manager_name=contact_name,
        company_name=company,
        job_description=job_description,
        company_url=company_url if company_url else None,
    )

    print("\n===== GENERATED EMAIL (preview) =====\n")
    print(email_html)
    print("\n=====================================\n")

    # Build a subject line
    subject = f"{job_title} – {company}"

    try:
        create_draft_with_resume(
            to_email=contact_email,
            subject=subject,
            html_body=email_html,
            resume_path=resume_path,
        )
        print(f"[DRAFT] Created Gmail draft to {contact_email} for '{job_title}' at {company}")
    except Exception as e:
        print(f"[ERROR] Failed to create draft for {contact_email}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Batch-create Gmail drafts from jobs_batch.csv")
    parser.add_argument(
        "--csv_path",
        required=True,
        help="Path to jobs_batch.csv (output of build_job_list.py)",
    )
    parser.add_argument(
        "--resume_path",
        required=False,
        default="docs/Sanyuja_Desai_Resume.pdf",
        help="Path to your resume PDF to attach to each draft.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)

    resume_path = Path(args.resume_path)
    if not resume_path.exists():
        print(f"[ERROR] Resume PDF not found at: {resume_path}")
        sys.exit(1)

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"[INFO] No rows in CSV: {csv_path}")
        return

    print(f"[INFO] Processing {len(rows)} rows from {csv_path}...\n")

    for idx, row in enumerate(rows, start=1):
        print(f"\n=== {idx}/{len(rows)} ===")
        process_row(row, str(resume_path))


if __name__ == "__main__":
    main()
