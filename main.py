# main.py

import argparse
import sys
from src.email_generator import draft_email
from src.gmail_draft import create_draft_with_resume


def main():
    parser = argparse.ArgumentParser(description="Draft hiring manager email")
    parser.add_argument("--title", required=True, help="Job Title")
    parser.add_argument("--url", required=True, help="Job Posting URL")
    parser.add_argument("--manager", required=True, help="Hiring Manager Name")
    parser.add_argument("--company", required=True, help="Company Name")
    parser.add_argument(
        "--jd_file",
        required=False,
        help="Path to a text file containing the full job description",
    )
    parser.add_argument(
        "--company_url",
        required=False,
        help="Company website URL (optional, for hyperlinking the company name)",
    )
    parser.add_argument(
        "--create_draft",
        action="store_true",
        help="If set, create a Gmail draft with this email and attached resume.",
    )
    parser.add_argument(
        "--to_email",
        required=False,
        help="Email address of the recipient for the Gmail draft.",
    )
    parser.add_argument(
        "--resume_path",
        required=False,
        default="docs/Sanyuja_Desai_Resume.pdf",
        help="Path to your resume PDF to attach to the draft.",
    )

    args = parser.parse_args()

    # Basic guard against placeholder inputs
    for field_name in ["title", "url", "manager", "company"]:
        value = getattr(args, field_name).strip()
        if not value or value == "...":
            print(f"[ERROR] --{field_name} cannot be empty or '...'. Please pass a real value.")
            sys.exit(1)

    job_description = ""
    if args.jd_file:
        try:
            with open(args.jd_file, "r", encoding="utf-8") as f:
                job_description = f.read().strip()
        except Exception as e:
            print(f"[WARN] Could not read job description file '{args.jd_file}': {e}")
            job_description = ""

    email_html = draft_email(
        job_title=args.title.strip(),
        job_url=args.url.strip(),
        hiring_manager_name=args.manager.strip(),
        company_name=args.company.strip(),
        job_description=job_description,
        company_url=args.company_url.strip() if args.company_url else None,
    )

    print("\n===== GENERATED EMAIL =====\n")
    print(email_html)
    print("\n===========================\n")

    if args.create_draft:
        if not args.to_email:
            print("[ERROR] --to_email is required when using --create_draft.")
            sys.exit(1)

        subject = f"Senior Data Scientist application – {args.company.strip()}"
        # You can tweak the subject line logic if you want:
        # subject = f"Application for {args.title.strip()} at {args.company.strip()}"

        try:
            create_draft_with_resume(
                to_email=args.to_email.strip(),
                subject=subject,
                html_body=email_html,
                resume_path=args.resume_path.strip(),
            )
        except Exception as e:
            print(f"[ERROR] Failed to create Gmail draft: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
