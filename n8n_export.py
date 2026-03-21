# n8n_export.py
# Exports last 24 hours of clean jobs as JSON with Category field.
# Category is used by n8n Switch node to route to correct Sheet tab.

import sys, json, os, io, contextlib
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from database import get_connection, init_db
from config import MIN_QUALITY_SCORE

with contextlib.redirect_stdout(io.StringIO()):
    init_db()

# ── Category mapping ──────────────────────────────────────────
# Keywords in job TITLE that determine which sheet it goes to.
# Order matters -- first match wins.
CATEGORY_RULES = [
    ("Cybersecurity", [
        "cybersecurity", "cyber security", "information security",
        "security analyst", "infosec", "penetration", "pentest",
    ]),
    ("Data & Analytics", [
        "data scientist", "data science", "data analyst", "data analytics",
        "machine learning", "ml engineer", "analytics engineer",
    ]),
    ("Design & Creative", [
        "ui", "ux", "designer", "graphic", "web design", "video editor",
        "motion graphic", "webflow", "wordpress", "visual designer",
        "product designer",
    ]),
    ("Marketing & Sales", [
        "digital marketing", "digital marketer", "seo", "growth marketer",
        "affiliate", "sales", "business development", "lead generation",
        "marketing manager", "marketing specialist",
    ]),
    ("Operations & HR", [
        "project manager", "scrum master", "product manager",
        "hr manager", "human resource", "talent acquisition", "recruiter",
        "customer service", "customer support", "customer experience",
        "virtual assistant", "data entry", "administrative",
        "microsoft office", "office assistant",
    ]),
    ("Tech & Engineering", [
        "software engineer", "software developer", "backend", "frontend",
        "full stack", "fullstack", "web developer", "python developer",
        "python engineer", "ai engineer", "ai automation", "automation engineer",
        "llm", "rag", "langchain", "crewai", "devops", "cloud engineer",
        "mobile developer", "ios", "android", "react", "node",
    ]),
]

DEFAULT_CATEGORY = "Other"


def categorise(title: str) -> str:
    """Return the sheet category for a job title."""
    title_lower = title.lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in title_lower for kw in keywords):
            return category
    return DEFAULT_CATEGORY


def _fmt_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(raw[:16], fmt).strftime("%B %d, %Y")
        except ValueError:
            continue
    return raw[:10]


def _fmt_verified(val) -> str:
    if val == 1: return "Yes"
    if val == 0: return "No"
    return "Pending"


cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")

conn = get_connection()
rows = conn.execute("""
    SELECT id, source, title, company, location, salary, remote,
           tech_stack, quality_score, date_posted, date_found,
           url, verified, scam_flag, description
    FROM jobs
    WHERE date_found >= ?
      AND (scam_flag IS NULL OR scam_flag = '')
      AND (quality_score IS NULL OR quality_score >= ?)
      AND (still_active IS NULL OR still_active = 1)
    ORDER BY quality_score DESC, date_found DESC
    LIMIT 500
""", (cutoff, MIN_QUALITY_SCORE)).fetchall()
conn.close()

jobs = []
for r in rows:
    jobs.append({
        "ID":           r[0]  or "",
        "Source":       r[1]  or "",
        "Title":        r[2]  or "",
        "Company":      r[3]  or "",
        "Location":     r[4]  or "",
        "Salary":       r[5]  or "",
        "Remote":       r[6]  or "",
        "Tech Stack":   r[7]  or "",
        "Score":        r[8]  if r[8] is not None else "",
        "Date Posted":  _fmt_date(r[9]  or ""),
        "Date Found":   _fmt_date(r[10] or ""),
        "URL":          r[11] or "",
        "Verified":     _fmt_verified(r[12]),
        "Description":  (r[14] or "")[:300],
        "Category":     categorise(r[2] or ""),
    })

print(json.dumps(jobs))