# src/contact_enricher.py

import os
import urllib.parse
from typing import List, Dict

import requests


HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

HUNTER_DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"


# Titles we care about
ROLE_KEYWORDS = [
    "data",
    "machine learning",
    "ml",
    "ai",
    "analytics",
    "science",
    "scientist",
    "recruiter",
    "talent",
    "people",
    "hiring",
    "engineering manager",
    "head of",
    "vp",
    "director",
]


def _extract_domain(company_url: str, company_domain: str | None) -> str | None:
    if company_domain and company_domain.strip():
        return company_domain.strip()

    if not company_url:
        return None

    try:
        parsed = urllib.parse.urlparse(company_url)
        host = parsed.netloc or parsed.path
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host or None
    except Exception:
        return None


def _score_contact(position: str | None) -> int:
    if not position:
        return 0
    pos = position.lower()
    score = 0
    for kw in ROLE_KEYWORDS:
        if kw in pos:
            score += 1
    return score


def _fallback_contact(company_name: str, domain: str | None) -> List[Dict[str, str]]:
    """
    Fallback when Hunter fails: create a generic contact.
    This is ONLY for testing your pipeline. You can replace this
    with something else later.
    """
    if not domain:
        return []
    fake_email = f"jobs@{domain}"
    print(f"[HUNTER-FALLBACK] Using generic contact {fake_email} for {company_name}")
    return [
        {
            "name": "Hiring Manager",
            "email": fake_email,
            "position": "Hiring Manager",
            "score": 1,
        }
    ]


def find_contacts_for_company(
    company_name: str,
    company_url: str | None = None,
    company_domain: str | None = None,
    max_contacts: int = 5,
) -> List[Dict[str, str]]:
    """
    Use Hunter's domain search to find relevant people to email at this company.
    Returns up to `max_contacts` contacts: name, email, position.

    If HUNTER_API_KEY is missing or Hunter returns an error, we
    fall back to a generic 'Hiring Manager' contact using jobs@domain.
    """
    domain = _extract_domain(company_url or "", company_domain)

    if not HUNTER_API_KEY:
        print("[HUNTER] HUNTER_API_KEY not set; using fallback contact.")
        return _fallback_contact(company_name, domain)

    if not domain:
        print(f"[HUNTER] Could not determine domain for {company_name}, skipping.")
        return []

    params = {
        "domain": domain,
        "api_key": HUNTER_API_KEY,
        "limit": 50,  # we'll filter client-side
    }

    try:
        resp = requests.get(HUNTER_DOMAIN_SEARCH_URL, params=params, timeout=15)
        # Try to parse JSON error for better debug if status not ok
        if resp.status_code != 200:
            try:
                err_json = resp.json()
                print(
                    f"[HUNTER] Non-200 response for domain={domain}: "
                    f"status={resp.status_code}, body={err_json}"
                )
            except Exception:
                print(
                    f"[HUNTER] Non-200 response for domain={domain}: "
                    f"status={resp.status_code}, raw_body={resp.text[:300]}"
                )
            # Use fallback contact so pipeline still works
            return _fallback_contact(company_name, domain)

        data = resp.json()
    except Exception as e:
        print(f"[HUNTER] Error calling Hunter for domain={domain}: {e}")
        # Use fallback on any error
        return _fallback_contact(company_name, domain)

    emails = data.get("data", {}).get("emails", [])
    if not emails:
        print(f"[HUNTER] No emails found for domain={domain}, using fallback.")
        return _fallback_contact(company_name, domain)

    scored = []
    for e in emails:
        email = e.get("value")
        if not email:
            continue
        position = e.get("position") or ""
        full_name = " ".join(filter(None, [e.get("first_name"), e.get("last_name")])).strip()

        score = _score_contact(position)
        if score == 0:
            continue

        scored.append(
            {
                "name": full_name or "",
                "email": email,
                "position": position,
                "score": score,
            }
        )

    if not scored:
        print(f"[HUNTER] No relevant-role contacts found for domain={domain}, using fallback.")
        return _fallback_contact(company_name, domain)

    # Sort by score (desc) and keep top N
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:max_contacts]

    print(f"[HUNTER] Selected {len(top)} contacts for {company_name} ({domain})")
    return top
