from src.email_generator import draft_email

def main():
    # Temporary example inputs
    job_title = "Senior Data Scientist"
    job_url = "https://example.com/job-posting"
    hiring_manager_name = "Alex Johnson"
    company_name = "Blue Rose Research"
    your_summary = """
    Lead Data Scientist with 7+ years experience in ML, experimentation,
    and LLM-based workflows. Built and deployed production systems,
    led cross-functional projects, and mentored junior engineers.
    """
    
    email_text = draft_email(
        job_title,
        job_url,
        hiring_manager_name,
        company_name,
        your_summary.strip()
    )

    print("\n===== GENERATED EMAIL =====\n")
    print(email_text)
    print("\n===========================\n")

if __name__ == "__main__":
    main()
