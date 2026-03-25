import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    "https://www.google.com/alerts/feeds/01468691923227883564/1509825071666675437",
    "https://www.google.com/alerts/feeds/01468691923227883564/2363373608580205622",
    "https://www.google.com/alerts/feeds/01468691923227883564/13130031224338349526",
    "https://www.google.com/alerts/feeds/01468691923227883564/9834271075784157347",
    "https://www.google.com/alerts/feeds/01468691923227883564/10474363077640805220",
    "https://www.google.com/alerts/feeds/01468691923227883564/10067902513436386819",
    "https://www.google.com/alerts/feeds/01468691923227883564/6007191438581647513",
    "https://www.google.com/alerts/feeds/01468691923227883564/18035095860822861221",
    "https://www.google.com/alerts/feeds/01468691923227883564/14190269149194048047",
    "https://www.google.com/alerts/feeds/01468691923227883564/11730920047306232995",
]

# ── Additional RSS feeds for new scrapers ─────────────────────
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
    # Example: "https://weworkremotely.com/categories/remote-programming-jobs.rss"
]

JOBSPRESSO_FEEDS = [
    # Disabled — Jobspresso removed from pipeline per user request
]

WORKING_NOMADS_FEEDS = [
    "https://www.workingnomads.co/api/exposed_jobs/"
]

# Himalayas API queries used by the Himalayas scraper
HIMALAYAS_QUERIES = [
    "web designer",
    "web developer",
    "data scientist",
    "ux designer",
    "virtual assistant",
    "cybersecurity",
    "digital marketing",
    "caregiver",
    "intern",
]

# Suggested Google Alerts queries (paste each into google.com/alerts and create RSS feeds)
# These six queries cover the target categories and restrict to Nigeria or Remote.
GOOGLE_ALERT_QUERIES = [
    # Web Design
    '("web designer" OR "web design" OR webflow OR figma) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    # Web Development
    '("web developer" OR frontend OR backend OR react OR vue) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    # Data Science & Analytics
    '("data scientist" OR "data analyst" OR "data analytics" OR "machine learning") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    # Graphics & UI/UX Design
    '("ux designer" OR "ui designer" OR "graphic designer" OR "product designer") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    # Virtual Assistant
    '("virtual assistant" OR "administrative assistant" OR "data entry") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    # Cybersecurity
    '("cybersecurity" OR "security analyst" OR infosec OR pentest) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
]

# OPTIONAL: Sponsorship-focused Google Alerts for UK/Canada (include "visa sponsorship" in query)
# GOOGLE_ALERT_QUERIES_SPONSORSHIP = [
#     '("web developer" OR frontend OR react) ("visa sponsorship" OR "sponsorship" OR "relocation") (United Kingdom OR UK)',
#     '("data scientist" OR "machine learning") ("visa sponsorship" OR "sponsorship" OR "relocation") (Canada)',
# ]

# LinkedIn-specific alert queries. Google Alerts can index LinkedIn public job pages;
# use the site: operator to bias results toward LinkedIn postings (paste these into Alerts).
GOOGLE_ALERT_QUERIES_LINKEDIN = [
    '(site:linkedin.com/jobs) ("web designer" OR "web design" OR webflow OR figma) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    '(site:linkedin.com/jobs) ("web developer" OR frontend OR backend OR react OR vue) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    '(site:linkedin.com/jobs) ("data scientist" OR "data analyst" OR "data analytics" OR "machine learning") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    '(site:linkedin.com/jobs) ("ux designer" OR "ui designer" OR "graphic designer" OR "product designer") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    '(site:linkedin.com/jobs) ("virtual assistant" OR "administrative assistant" OR "data entry") (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
    '(site:linkedin.com/jobs) ("cybersecurity" OR "security analyst" OR infosec OR pentest) (job OR hiring OR vacancy) (Nigeria OR Lagos OR Abuja OR "work from home" OR remote)',
]

# ── 2. INDEED SEARCHES ────────────────────────────────────────
# Indeed searches removed — we rely on Google Alerts / APIs and
# post-scrape filtering to avoid scraping Indeed directly (Indeed blocks scraping).


# ── 3. REMOTEOK TAGS ──────────────────────────────────────────
# RemoteOK tags that map to your target roles
REMOTEOK_TAGS = [
    # Narrow tags to the six target categories
    "developer", "web", "frontend", "react", "vue", "backend",
    "design", "ux", "ui", "graphic", "product",
    "data", "machine-learning", "security", "virtual-assistant",
    # Add marketing and healthcare-related tags for other sources
    "marketing", "seo", "social-media", "healthcare", "caregiver",
]

# ── 4. HACKER NEWS ────────────────────────────────────────────
HACKERNEWS_ENABLED = True

# ── 5. KEYWORD FILTER ─────────────────────────────────────────
# A job title must contain at least ONE of these words to be saved.
# This prevents irrelevant results from wasting AI credits.
TARGET_KEYWORDS = [
    # Focused on the six target categories (see README / plan)
    # Web Design
    "web designer", "webflow", "figma", "ui designer", "website design",
    # Web Development
    "web developer", "frontend", "backend", "fullstack", "full stack",
    "react", "vue", "angular", "node", "javascript", "php",
    # Data Science & Analytics
    "data scientist", "data analyst", "data analytics", "analytics",
    "machine learning", "ml", "ml engineer",
    # Graphics & UI/UX Design
    "ux designer", "ui ux", "ui/ux", "graphic designer", "visual designer",
    "product designer", "motion graphic", "visual design",
    # Virtual Assistant
    "virtual assistant", "administrative assistant", "data entry",
    # Cybersecurity
    "cybersecurity", "security analyst", "information security", "infosec",
    "penetration", "pentest", "security engineer",
    # Internship / trainee terms (include internships within the target categories)
    "intern", "internship", "siwes", "trainee", "graduate",
    # Broader terms and common tech/shop keywords to increase recall
    "engineer", "developer", "software", "dev",
    "junior", "entry-level", "entry level", "associate",
    "python", "django", "flask", "nodejs", "node", "typescript",
    "sql", "postgres", "mysql", "mongodb", "firebase", "aws", "azure", "gcp",
    "docker", "kubernetes", "devops", "site reliability", "sre",
    "css", "html", "scss", "sass", "figma", "sketch", "adobe", "photoshop", "illustrator",
    "seo", "sem", "content", "social media", "ppc", "email marketing", "growth",
    "excel", "powerbi", "tableau", "r", "spark", "hadoop", "etl",
    "support", "customer support", "technical support", "virtual assistant", "va",
    "security", "infosec", "pentest", "penetration", "sre", "soc", "cloud security",
]

# ── 6. REMOTIVE CATEGORIES ───────────────────────────────────
REMOTIVE_CATEGORIES = [
    # Keep only categories relevant to the six targets
    "software-dev",
    "data",
    "design",
    "customer-support",  # used for virtual assistant roles
    "marketing",
    # Note: Remotive may not have a dedicated healthcare category; Google Alerts will cover caregiver roles
]

# ── 7. OUTPUT ─────────────────────────────────────────────────
DB_PATH = "/data/jobs.db"
EXCEL_PATH = "/data/jobs_output.xlsx"
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

# ── Location filtering: allow only jobs that match these location terms
# Matches are case-insensitive substrings of the extracted location field.
ALLOWED_LOCATIONS = [
    "Nigeria",
    # common Nigerian cities / states (keeps local roles)
    "Lagos", "Abuja", "Port Harcourt", "Kano", "Ibadan", "Enugu",
    "Benin", "Jos", "Kaduna", "Warri", "Owerri", "Uyo", "Zaria",
    "Ilorin", "Abeokuta",
    # Remote
    "Remote", "Work from Home", "WFH", "Work-from-Home", "Telecommute",
]

# Toggle enforcement. Set False to disable location filtering.
ENFORCE_LOCATION_FILTER = True

# ── 8. CATEGORY RULES ─────────────────────────────────────────
CATEGORY_RULES = [
    ("Web Design", [
        "web designer", "web design", "website design", "webflow", "landing page",
        "squarespace", "wix", "framer",
    ]),
    ("Web Development", [
        "web developer", "frontend", "backend", "fullstack", "full stack",
        "react", "vue", "angular", "node", "javascript", "php",
        "django", "flask", "nodejs", "python", "developer", "software engineer",
        "engineer", "wordpress", "java", "ruby", "golang", "c#", "api"
    ]),
    ("Data Science & Analytics", [
        "data scientist", "data analyst", "data analytics", "analytics",
        "machine learning", "ml", "ml engineer",
        "data", "tableau", "powerbi", "spark", "hadoop", "python", "sql", "etl"
    ]),
    ("Graphics & UI/UX", [
        "ux designer", "ui designer", "ui ux", "ui/ux", "ux/ui", "graphic designer",
        "graphic design", "product designer", "visual designer", "visual design",
        "brand designer", "brand design", "motion graphic", "photoshop", "illustrator",
        "adobe", "sketch", "figma", "digital designer", "creative designer"
    ]),
    ("Virtual Assistant", [
        "virtual assistant", "administrative assistant", "data entry", "va",
        "admin", "executive assistant", "personal assistant"
    ]),
    ("Cybersecurity", [
        "cybersecurity", "security analyst", "information security", "infosec",
        "penetration", "pentest", "security engineer",
        "cloud security", "sre", "soc",
    ]),
    ("Internship", [
        "intern", "internship", "siwes", "trainee", "graduate",
    ]),
    ("Digital Marketing", [
        "digital marketing", "digital marketer", "seo", "social media", "content marketing",
        "growth marketer", "social-media", "email marketing", "marketing", "ads",
        "advertising", "campaigns", "ppc", "performance marketing", "product marketing", "media buyer"
    ]),
    ("Caregiver/Health Care Assistant", [
        "caregiver", "care assistant", "healthcare assistant", "home care", "care home",
        "nursing assistant", "health care assistant",
    ]),
]
