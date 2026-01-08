from openai import OpenAI
from .config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def draft_email(job_title, job_url, hiring_manager_name, company_name, your_summary):
    """
    Creates a short outreach email to hiring manager.
    """

    prompt = f"""
Write a concise, warm outreach email to a hiring manager.

Details:
- Job Title: {job_title}
- Job Link: {job_url}
- Hiring Manager: {hiring_manager_name}
- Company: {company_name}

Candidate Background:
{your_summary}

Requirements:
- Reference the job title AND the job link.
- Say *why* I fit based on my background.
- Ask kindly for guidance or a short conversation.
- Under 200 words.
    """

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You write concise, friendly emails."},
            {"role": "user", "content": prompt}
        ],
    )

    return completion.choices[0].message.content.strip()
