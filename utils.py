# ─────────────────────────────────────────────────────────────
# utils.py  —  Shared helpers used by all scrapers
# ─────────────────────────────────────────────────────────────

import requests
import re
from datetime import datetime
from config import TARGET_KEYWORDS


# ── Text Cleaners ─────────────────────────────────────────────

def strip_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&quot;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_text(text: str, max_len: int = 500) -> str:
    return strip_html(text)[:max_len]


# ── Field Extractors ──────────────────────────────────────────

def extract_salary(text: str) -> str:
    """Pull salary range from raw text."""
    patterns = [
        r"\$[\d,]+\s*[-–to]+\s*\$[\d,]+",   # $100,000 - $150,000
        r"\$[\d,]+[kK]\s*[-–to]+\s*\$[\d,]+[kK]",  # $100k - $150k
        r"\$[\d,]+\+?\s*(?:per year|/yr|annually)?",  # $120,000/yr
        r"[\d,]+\s*[-–]\s*[\d,]+\s*USD",    # 100,000 - 150,000 USD
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return ""


def extract_location(text: str) -> str:
    """Extract location hint from text."""
    # Check remote first
    if re.search(r"\bremote\b", text, re.IGNORECASE):
        # Check if it's hybrid
        if re.search(r"hybrid", text, re.IGNORECASE):
            return "Hybrid / Remote"
        return "Remote"

    # Common city names
    cities = [
        "New York", "San Francisco", "Seattle", "Austin", "Boston",
        "Chicago", "Los Angeles", "Denver", "Atlanta", "Miami",
        "Toronto", "London", "Berlin", "Amsterdam", "Singapore",
        "Lagos", "Nairobi", "Dubai", "Sydney", "Bangalore",
    ]
    for city in cities:
        if city.lower() in text.lower():
            return city
    return ""


def is_remote(text: str) -> str:
    """Return 'Yes', 'Hybrid', or 'No'."""
    text_lower = text.lower()
    if "hybrid" in text_lower:
        return "Hybrid"
    if re.search(r"\bremote\b", text_lower):
        return "Yes"
    return "No"


def parse_date(raw: str) -> str:
    """Normalise various date formats to YYYY-MM-DD."""
    if not raw:
        return datetime.now().strftime("%Y-%m-%d")
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw[:30].strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")


# ── Keyword Filter ────────────────────────────────────────────

def passes_keyword_filter(title: str) -> bool:
    """
    Return True if the job title contains at least one target keyword.
    Skips the AI call for irrelevant postings — saves API credits.
    If TARGET_KEYWORDS is empty, everything passes.
    """
    if not TARGET_KEYWORDS:
        return True
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in TARGET_KEYWORDS)


# ── HTTP Helper ───────────────────────────────────────────────


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str, timeout: int = 15) -> requests.Response | None:
    """GET request with retries and shared headers. Never retries 4xx errors."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            # 4xx = client errors — retrying won't help, bail immediately
            print(f"    ✗ {e}")
            return None
        except requests.RequestException as e:
            if attempt == 2:
                print(f"    ✗ Failed after 3 attempts: {url[:60]} — {e}")
            else:
                import time
                time.sleep(2)
    return None
