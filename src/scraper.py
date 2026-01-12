# src/scraper.py

import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _clean_text(text: str) -> str:
    # Normalize whitespace, remove super-long runs of blank lines
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # collapse >2 blank lines
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_job_block(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to find the main job description block.
    We look for div/section/article whose id/class mention 'job' or 'description'
    and pick the longest reasonable one.
    """
    candidates = []

    for tag in soup.find_all(["section", "div", "article"]):
        attrs = " ".join(
            [
                tag.get("id", ""),
                " ".join(tag.get("class", [])),
            ]
        ).lower()

        if any(k in attrs for k in ["job", "description", "posting", "position", "content", "main"]):
            text = tag.get_text(separator="\n", strip=True)
            if len(text) > 400:  # ignore tiny blocks
                candidates.append(text)

    if candidates:
        # pick the longest candidate
        best = max(candidates, key=len)
        return best

    # Fallback: just use the whole body
    if soup.body:
        return soup.body.get_text(separator="\n", strip=True)

    return None


def fetch_job_description(url: str, max_chars: int = 8000) -> str:
    """
    Fetch the job description text from a URL.

    This is a best-effort scraper:
    - Makes a GET request with a real-ish User-Agent
    - Parses HTML with BeautifulSoup
    - Tries to extract the main job content
    - Cleans and truncates to max_chars for model usage
    """
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[SCRAPER] Error fetching URL {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    raw_text = _extract_job_block(soup)
    if not raw_text:
        print(f"[SCRAPER] Could not extract main job block for {url}, using raw page text.")
        raw_text = soup.get_text(separator="\n", strip=True)

    cleaned = _clean_text(raw_text)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[truncated]"
    return cleaned
