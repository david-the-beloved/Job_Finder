# ─────────────────────────────────────────────────────────────
# config.py  —  Edit this file to customise your scraper
# ─────────────────────────────────────────────────────────────

# ── 1. GOOGLE ALERTS ─────────────────────────────────────────
# Go to google.com/alerts → create an alert → click ⚙ → set
# delivery to "RSS feed" → paste the URL below.
# Tip: create 20-50 alerts for best coverage.
GOOGLE_ALERT_FEEDS = [
    # "https://www.google.com/alerts/feeds/YOUR_ACCOUNT_ID/YOUR_ALERT_ID",
    # Add as many as you want — each is a separate search query
]

# ── 2. INDEED SEARCHES ───────────────────────────────────────
# Each dict is one search. Add/remove roles and locations freely.
INDEED_SEARCHES = [
    {"q": "software engineer",    "l": "remote"},
    {"q": "backend developer",    "l": "remote"},
    {"q": "frontend developer",   "l": "remote"},
    {"q": "full stack developer", "l": "remote"},
    {"q": "data scientist",       "l": "remote"},
    {"q": "product manager",      "l": "remote"},
    {"q": "devops engineer",      "l": "remote"},
    {"q": "machine learning engineer", "l": "remote"},
]

# ── 3. REMOTEOK TAGS ─────────────────────────────────────────
# Filter RemoteOK by tag. Leave empty [] to get all jobs.
REMOTEOK_TAGS = ["engineer", "dev", "python", "react", "manager"]

# ── 4. HACKER NEWS ───────────────────────────────────────────
# Scrapes the monthly "Who's Hiring" thread.
# Nothing to configure — runs automatically.
HACKERNEWS_ENABLED = True

# ── 5. KEYWORD FILTER ────────────────────────────────────────
# Jobs whose title does NOT contain any of these words are
# skipped before hitting the AI — saves API credits.
# Set to [] to collect everything.
TARGET_KEYWORDS = [
    "engineer", "developer", "scientist", "manager",
    "designer", "analyst", "architect", "lead", "devops",
]

# ── 6. OUTPUT ─────────────────────────────────────────────────
DB_PATH     = "data/jobs.db"         # SQLite database
EXCEL_PATH  = "data/jobs_output.xlsx"  # Excel export

# ── 7. GEMINI API (optional — for AI verification later) ─────
# Leave empty for now — we add this in Phase 2
GEMINI_API_KEY = ""
