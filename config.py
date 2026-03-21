import os
from dotenv import load_dotenv

load_dotenv()

# config.py -- Your personalised job scraper config
# Targeting: Nigeria + Remote | All your 20 role categories

# ── 1. GOOGLE ALERTS ──────────────────────────────────────────
# HOW TO SET UP (one-time, 10 mins):
#   1. Go to google.com/alerts
#   2. Paste each query below into the search box
#   3. Click "Show options" -> Delivery: RSS feed, How often: As-it-happens
#      Sources: Automatic, Language: English, Region: Any Region
#      How many: All results
#   4. Click "Create Alert"
#   5. Copy the RSS URL that appears -> paste into the list below
#
# PASTE YOUR 20 RSS URLS HERE after creating the alerts:
GOOGLE_ALERT_FEEDS = [
    # -- Software & AI Engineering --
    # Query: ("AI Automation" OR "Automation Engineer" OR "AI Agent" OR "CrewAI" OR "LangChain") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/4197818390532235490",

    # Query: ("AI Engineering" OR "AI Engineer" OR "LLM" OR "RAG") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/9225487027929768142",

    # Query: ("Backend Development" OR "Backend Developer" OR "Backend Engineer" OR "FastAPI" OR "PostgreSQL") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/641582736709731395",

    # Query: ("Python Programming" OR "Python Developer" OR "Python Engineer") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/9873014383824638038",

    # Query: ("Software Engineering" OR "Software Engineer" OR "Software Developer") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/7239954670997390510",

    # -- Web & Design --
    # Query: ("Website Development" OR "Web Developer" OR "Frontend Developer" OR "React") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/16912204080919469312",

    # Query: ("Website Design" OR "Web Designer" OR "Webflow" OR "WordPress") AND ("job" OR "hiring" OR "internship") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/9450784462869828834",

    # Query: ("UI/UX Design" OR "UX Designer" OR "UI Designer" OR "Product Designer") AND ("job" OR "hiring" OR "internship") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/1860411076963337181",

    # Query: ("Graphic Design" OR "Graphic Designer" OR "Visual Designer") AND ("job" OR "hiring" OR "internship") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/17157149744000026465",

    # Query: ("Video Editing" OR "Video Editor" OR "Motion Graphics") AND ("job" OR "hiring" OR "internship") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/14604670319903036885",

    # -- Data & Security --
    # Query: ("Data Science" OR "Data Scientist" OR "Machine Learning" OR "Data Analytics" OR "Data Analyst") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/85202478982112756",

    # Query: ("Cybersecurity" OR "Cyber Security" OR "Information Security" OR "Security Analyst") AND ("job" OR "hiring" OR "internship" OR "SIWES") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/618360882686642336",

    # -- Business, Marketing & Operations --
    # Query: ("Sales" OR "Marketing" OR "Business Development" OR "Lead Generation") AND ("job" OR "hiring" OR "vacancy") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/11942330650386542042",

    # Query: ("Digital Marketing" OR "Digital Marketer" OR "SEO" OR "Growth Marketer" OR "Affiliate Marketing") AND ("job" OR "hiring" OR "internship") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/6780290350157594727",

    # Query: ("Human Resource Management" OR "HR Manager" OR "Human Resources" OR "Talent Acquisition") AND ("job" OR "hiring" OR "vacancy") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/15658136954935503802",

    # Query: ("Project Management" OR "Project Manager" OR "Scrum Master" OR "Product Manager") AND ("job" OR "hiring" OR "vacancy") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/16209577461149503278",

    # Query: ("Customer Service" OR "Customer Experience" OR "Customer Support" OR "CX") AND ("job" OR "hiring" OR "vacancy") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/3789525544071779490",

    # Query: ("Microsoft Office" OR "Data Entry" OR "Administrative Assistant" OR "Virtual Assistant") AND ("job" OR "hiring" OR "vacancy") AND ("Nigeria" OR "remote" OR "work from home" OR "WFH")
    "https://www.google.com/alerts/feeds/01468691923227883564/13735372367469499006",

    "https://www.google.com/alerts/feeds/01468691923227883564/9400277812245349921",

    "https://www.google.com/alerts/feeds/01468691923227883564/6336132768190135015",

    "https://www.google.com/alerts/feeds/01468691923227883564/8449500067692150583",

    "https://www.google.com/alerts/feeds/01468691923227883564/6659162664020009043",

    "https://www.google.com/alerts/feeds/01468691923227883564/18410914477435233343",
]

# ── 2. INDEED SEARCHES ────────────────────────────────────────
# Covers all 20 of your categories.
# "remote" catches global remote roles open to Nigeria.
# "Lagos" catches Nigeria-specific postings.
INDEED_SEARCHES = [
    # Software & AI Engineering
    {"q": "AI automation engineer",        "l": "remote"},
    {"q": "AI agent developer LangChain",  "l": "remote"},
    {"q": "AI engineer LLM",               "l": "remote"},
    {"q": "backend developer FastAPI",     "l": "remote"},
    {"q": "backend engineer Python",       "l": "remote"},
    {"q": "Python developer",              "l": "remote"},
    {"q": "software engineer",             "l": "remote"},
    {"q": "software developer",            "l": "Lagos"},

    # Web & Design
    {"q": "frontend developer React",      "l": "remote"},
    {"q": "web developer",                 "l": "remote"},
    {"q": "web designer Webflow",          "l": "remote"},
    {"q": "UI UX designer",                "l": "remote"},
    {"q": "product designer",              "l": "remote"},
    {"q": "graphic designer",              "l": "remote"},
    {"q": "graphic designer",              "l": "Lagos"},
    {"q": "video editor motion graphics",  "l": "remote"},

    # Data & Security
    {"q": "data scientist machine learning", "l": "remote"},
    {"q": "data analyst",                  "l": "remote"},
    {"q": "data analyst",                  "l": "Lagos"},
    {"q": "cybersecurity analyst",         "l": "remote"},
    {"q": "information security engineer", "l": "remote"},

    # Business, Marketing & Operations
    {"q": "digital marketing SEO",         "l": "remote"},
    {"q": "digital marketer",              "l": "Lagos"},
    {"q": "sales marketing Nigeria",       "l": "remote"},
    {"q": "business development",          "l": "Lagos"},
    {"q": "HR manager talent acquisition", "l": "remote"},
    {"q": "human resources",               "l": "Lagos"},
    {"q": "project manager",               "l": "remote"},
    {"q": "scrum master product manager",  "l": "remote"},
    {"q": "customer service support",      "l": "remote"},
    {"q": "customer experience",           "l": "Lagos"},
    {"q": "virtual assistant",             "l": "remote"},
    {"q": "data entry administrative",     "l": "remote"},
]

# ── 3. REMOTEOK TAGS ──────────────────────────────────────────
# RemoteOK tags that map to your target roles
REMOTEOK_TAGS = [
    "engineer", "developer", "python", "react", "backend",
    "frontend", "ai", "machine-learning", "data", "design",
    "ux", "marketing", "manager", "devops", "security",
    "customer-support", "video", "hr",
]

# ── 4. HACKER NEWS ────────────────────────────────────────────
HACKERNEWS_ENABLED = True

# ── 5. KEYWORD FILTER ─────────────────────────────────────────
# A job title must contain at least ONE of these words to be saved.
# This prevents irrelevant results from wasting AI credits.
TARGET_KEYWORDS = [
    # Tech roles
    "engineer", "developer", "programmer", "architect",
    "python", "backend", "frontend", "fullstack", "full stack",
    "ai", "automation", "machine learning", "llm", "rag",
    # Data
    "data", "analyst", "scientist", "analytics",
    # Design & Creative
    "designer", "design", "ux", "ui", "graphic", "video", "editor",
    "webflow", "wordpress", "web",
    # Security
    "security", "cybersecurity", "infosec",
    # Business & Ops
    "marketing", "seo", "digital", "sales", "business development",
    "hr", "human resource", "recruiter", "talent",
    "project manager", "product manager", "scrum",
    "customer service", "customer support", "customer experience",
    "virtual assistant", "data entry", "administrative",
    # SIWES / internship terms common in Nigeria
    "intern", "siwes", "trainee", "graduate",
]

# ── 6. REMOTIVE CATEGORIES ───────────────────────────────────
REMOTIVE_CATEGORIES = [
    "software-dev",       # Software Eng, Backend, Python, AI, Web Dev
    "data",               # Data Science, Data Analytics
    "design",             # UI/UX, Web Design, Graphic Design
    "marketing",          # Digital Marketing
    "sales",              # Sales & Marketing
    "product",            # Project Management
    "human-resources",    # HR Management
    "customer-support",   # Customer Service / CX
    "devops-sysadmin",    # Cybersecurity
    "writing",            # Video Editing
    "qa-testing",
    "finance-legal",
]

# ── 7. OUTPUT ─────────────────────────────────────────────────
DB_PATH = "data/jobs.db"
EXCEL_PATH = "data/jobs_output.xlsx"
GOOGLE_SERVICE_ACCOUNT_KEY = os.environ.get(
    "GOOGLE_SA_KEY_PATH", "data/service_account.json")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SHEETS_ENABLED = True

# ── 7. GEMINI AI VERIFICATION ─────────────────────────────────
# Get a free key at: aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# gemini-2.0-flash-lite = cheapest, fast, good enough for verification
GEMINI_MODEL = "gemini-2.5-flash-lite"

# Free tier = 20 RPD. Script auto-tracks and warns when exceeded.
GEMINI_FREE_RPD = 20

# Hard cap per run -- safety net. Raise once you're comfortable.
GEMINI_MAX_CALLS_PER_RUN = 100

# Tracks daily usage + cost across runs
GEMINI_QUOTA_FILE = "data/gemini_quota.json"

# Jobs below this score are hidden from Excel but kept in DB.
# Set to 1 to see everything including low-quality postings.
MIN_QUALITY_SCORE = 4
