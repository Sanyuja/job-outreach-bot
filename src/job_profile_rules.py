# src/job_profile_rules.py

import re


# Titles you WANT (rough heuristic – tweak as you like)
POSITIVE_KEYWORDS = [
    "data scientist",
    "senior data scientist",
    "staff data scientist",
    "machine learning engineer",
    "ml engineer",
    "applied scientist",
    "research scientist",
    "ml scientist",
    "quantitative researcher",
    "ml research engineer",
    "ai engineer",
    "ml ops",
    "mlops",
    "risk data scientist",
    "fraud data scientist",
    "risk modeling",
    "risk analytics",
    "Data Analyst"
]

# Titles you want to avoid
NEGATIVE_KEYWORDS = [
    "product manager",
    "account manager",
    "sales",
    "customer success",
    "frontend",
    "backend",
    "full stack",
    "marketing",
    "designer",
    "intern",
    "junior",
]


def normalize_title(title: str) -> str:
    return title.strip().lower()


def is_title_relevant(title: str) -> bool:
    """
    Simple heuristic:
    - Title must contain at least one POSITIVE keyword
    - And must NOT contain any NEGATIVE keyword
    """
    t = normalize_title(title)

    if any(bad in t for bad in NEGATIVE_KEYWORDS):
        return False

    if any(good in t for good in POSITIVE_KEYWORDS):
        return True

    # Optional: allow generic "data scientist" if nothing else matches
    if "data scientist" in t:
        return True

    return False


def guess_use_jd(job_url: str) -> str:
    """
    Decide whether to try scraping the JD from this URL.
    For now, we can skip LinkedIn (they're JS/login-heavy) and say 'no'.
    """
    url_low = job_url.lower()
    if "linkedin.com" in url_low:
        return "no"
    return "yes"
