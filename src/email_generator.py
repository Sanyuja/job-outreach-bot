# src/email_generator.py

import os
from openai import OpenAI
from dotenv import load_dotenv
from .profile import BACKGROUND
from .style_profile import load_style_profile
from .links import LINKEDIN_URL, PORTFOLIO_URL, GITHUB_URL

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in .env")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

try:
    STYLE_PROFILE = load_style_profile()
except Exception as e:
    print(f"[WARN] Could not load style profile: {e}")
    STYLE_PROFILE = {}


def _clean_body_text(raw: str) -> str:
    """
    Remove any greeting, signoff, name, or LinkedIn/GitHub/footer
    that the model might add, so we can control those ourselves.
    """
    # Split into lines and strip trailing whitespace
    lines = [line.rstrip() for line in raw.strip().splitlines()]

    # 1) Remove leading greeting lines like:
    #    "Hi Sam," / "Hi Sam Lee," / "Hello ..." / "Dear ..."
    start_idx = 0
    while start_idx < len(lines):
        l = lines[start_idx].strip()
        low = l.lower()

        if (
            low.startswith("hi ")
            or low.startswith("hello ")
            or low.startswith("dear ")
        ) and (low.endswith(",") or low.endswith(":")):
            # Skip this line and a following blank line if present
            start_idx += 1
            if start_idx < len(lines) and lines[start_idx].strip() == "":
                start_idx += 1
            continue
        break

    # Trim off any greetings
    lines = lines[start_idx:]

    # 2) Filter out signoffs, names, and footer-y lines anywhere
    filtered = []
    signoff_phrases = {
        "thanks",
        "thanks,",
        "thank you",
        "thank you,",
        "best",
        "best,",
        "sincerely",
        "sincerely,",
        "kind regards",
        "kind regards,",
        "regards",
        "regards,",
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # We'll remove extra blanks at the end, but keep some spacing in body
            filtered.append(stripped)
            continue

        low = stripped.lower()

        # Bracketed placeholder/footer lines like:
        # [Resume attached as a file], [Your LinkedIn Profile: ...], etc.
        if low.startswith("[") and low.endswith("]"):
            continue

        # Any line that appears to just be your name (or includes it)
        if "sanyuja" in low:
            continue

        # Common signoff phrases
        if low in signoff_phrases:
            continue

        # Link/footer lines mentioning LinkedIn/GitHub explicitly
        if "linkedin" in low or "github" in low:
            continue

        filtered.append(stripped)

    # Remove leading/trailing blank lines and collapse
    cleaned = []
    for l in filtered:
        if l == "" and (not cleaned or cleaned[-1] == ""):
            # collapse multiple blank lines
            continue
        cleaned.append(l)

    # Strip trailing blank lines
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    # Final collapse
    cleaned = [l for l in cleaned if l.strip() != "" or l == ""]
    # Join non-empty logical lines with newlines (paragraphs)
    return "\n".join([l for l in cleaned if l != ""])


def _format_email_html(hiring_manager_name: str, body_text: str) -> str:
    """
    Wrap cleaned body text in a consistent HTML email:

    Hi {Manager},

    [body]

    Thanks,
    Sanyuja
    """
    # Turn body into paragraphs separated by <br><br>
    lines = [line.strip() for line in body_text.strip().split("\n") if line.strip()]
    body_html = "<br><br>".join(lines)

    greeting = f"Hi {hiring_manager_name},<br><br>"
    closing = "<br><br>Thanks,<br>Sanyuja"

    return f"{greeting}{body_html}{closing}"


def draft_email(
    job_title: str,
    job_url: str,
    hiring_manager_name: str,
    company_name: str,
    job_description: str = "",
    company_url: str | None = None,
):
    """
    Writes a personalized outreach email that:
    - Uses Sanyuja's real background (BACKGROUND)
    - Uses her learned style profile (STYLE_PROFILE) if available
    - Analyzes the job description (if provided) to highlight genuine matches
    - Mentions that her resume is attached
    - Uses clean HTML-friendly hyperlinks for the job, company (if given), and her own links
    - Always formats greeting + signoff as:

        Hi {Manager},

        [body]

        Thanks,
        Sanyuja
    """

    style_json_str = str(STYLE_PROFILE)

    # HTML hyperlink for the job posting
    job_link_html = f'<a href="{job_url}">{job_title}</a>'

    # Optional HTML hyperlink for the company name
    if company_url:
        company_html = f'<a href="{company_url}">{company_name}</a>'
    else:
        company_html = company_name

    # HTML links for your personal sites (only if non-empty)
    personal_links_lines = []
    if LINKEDIN_URL:
        personal_links_lines.append(f'LinkedIn: <a href="{LINKEDIN_URL}">{LINKEDIN_URL}</a>')
    if PORTFOLIO_URL:
        personal_links_lines.append(f'Portfolio: <a href="{PORTFOLIO_URL}">{PORTFOLIO_URL}</a>')
    if GITHUB_URL:
        personal_links_lines.append(f'GitHub: <a href="{GITHUB_URL}">{GITHUB_URL}</a>')

    personal_links_block = "\n".join(personal_links_lines) if personal_links_lines else "None provided."

    prompt = f"""
You are acting as *Sanyuja Desai*.

==== BACKGROUND (RESUME) ====
{BACKGROUND}

==== STYLE PROFILE (JSON, MAY BE EMPTY) ====
{style_json_str}

==== JOB DESCRIPTION (MAY BE EMPTY) ====
{job_description}

==== PERSONAL LINKS (HTML) ====
{personal_links_block}

CONTEXT:
- Role: {job_title}
- Role Hyperlink: {job_link_html}
- Company: {company_html}
- Job Posting URL (raw): {job_url}

TASK:
Write ONLY the main body of an outreach email to this hiring manager.

DO NOT:
- Do NOT include any greeting at the top (no "Hi Sam," or similar).
- Do NOT include any signoff or name at the bottom (no "Thanks," "Best," "Sanyuja", etc.).
- Do NOT include raw footer lines like "[Your LinkedIn Profile: ...]" or standalone LinkedIn/GitHub URLs.
- Do NOT restate your name; the system will add the signature.

The system will add "Hi {hiring_manager_name}," at the top and "Thanks, Sanyuja" at the bottom.

- Hiring Manager: {hiring_manager_name}
- Company: {company_name}
- Role: {job_title}

BODY WRITING RULES:
- Write in first-person ("I") as Sanyuja.
- Do NOT include any greeting at the top.
- Do NOT include any signoff or name at the bottom.
- Match the tone implied by STYLE_PROFILE.
- Absolutely avoid em dashes (—). Use commas or short sentences instead.
- Use correct grammar. Always say “the next steps” instead of “next steps” and similar definite-article cases.
- Prefer standard professional phrasing. Avoid casual contractions and filler phrases.
- When referencing the role, you may refer to it as {job_link_html}.
- Explicitly mention that her resume is attached.
- Highlight 2–3 real overlaps between her background and the JD.
- Invite a short call or ask for guidance on the next steps.
- Keep the body under ~150 words.
- Avoid generic corporate clichés and avoid sounding desperate or apologetic.
- The output should be plain text that can be sent as an email, but may contain simple HTML like <a href="...">text</a>.
    """

    try:
        completion = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "Write as Sanyuja in first-person, following her style profile and background. Only output the body of the email, no greeting or signoff.",
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as e:
        print(f"[ERROR] OpenRouter chat.completions.create failed: {e}")
        return "[ERROR] Failed to generate email. Check OPENROUTER_API_KEY, network, or model name."

    content = completion.choices[0].message.content
    if not content or not content.strip():
        print("[WARN] Model returned empty content.")
        return "[WARN] Model returned empty content. Try a different model or check request."

    cleaned_body = _clean_body_text(content)
    return _format_email_html(hiring_manager_name, cleaned_body)
