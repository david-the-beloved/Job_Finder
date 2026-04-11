# Job Finder — Automated Job Scraper & n8n Google Sheets Export

## Purpose

This repository automates finding recent entry-level / junior-friendly jobs (and internships) across free job sources, filters them for Nigeria or remote roles, categorises them into target areas (Web Development, Web Design, Data Science & Analytics, Graphics & UI/UX, Virtual Assistant, Cybersecurity, Digital Marketing, Internship, Caregiver/Health Care Assistant), and appends only new jobs to Google Sheets via an n8n workflow.

The goal: remove manual labour of scanning job boards after a course finishes — this runs on schedule and keeps a central sheet populated with fresh, deduplicated listings.

## Contents

- `main.py` — orchestrates scraping runs and persisting normalized jobs to the local DB.
- `api.py` — FastAPI app that exposes job endpoints for n8n (unsynced jobs, mark-as-synced, listing, stats).
- `database.py` — SQLite helpers and schema (`jobs` table includes `synced_to_sheets` flag).
- `config.py` — centralised feed lists, target keywords, allowed locations, and other settings.
- `utils.py` — parsing helpers, filtering logic, HTTP fetch helpers.
- `scrapers/` — per-source scrapers (WorkingNomads API, WWR RSS, Himalayas API, RemoteOK shim, Remotive, HackerNews, etc.).
- `Job Scraper - Multi Sheet Export.json` — n8n workflow (import into n8n) that fetches unsynced jobs and appends them to different Google Sheets tabs.
- `data/service_account.json` — (not committed) Google service account for Sheets access (keep secure).

## Quick Architecture Summary

1. Scheduled scraper run (via a scheduler or manual run) inserts normalized job records into the SQLite DB.
2. `synced_to_sheets` defaults to false for new records.
3. n8n workflow polls `GET /jobs/unsynced?hours=24` to fetch unsynced jobs (last 24h by default), appends them to the correct Google Sheets tab according to `Category`, and then calls `POST /jobs/mark_synced` with the appended job IDs so the system doesn't re-append duplicates.

## Prerequisites

- Python 3.10+ (or 3.8+ — check `requirements.txt`).
- `pip` and a virtual environment.
- `n8n` instance (local or hosted) with Google Sheets credentials configured.
- Google Sheets document ID and a service account with Editor rights to the sheet.

## Setup (local)

1. Create and activate virtualenv (Windows PowerShell):

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

2. Place your service account JSON at `data/service_account.json` (or update `config.py` with path).
3. Update `config.py`:
   - `GOOGLE_SHEET_ID` — your sheet ID.
   - `ALLOWED_LOCATIONS` and `TARGET_KEYWORDS` if you want to tweak matching.
4. (Optional) Run a syntax check before running:

```powershell
python -m py_compile config.py utils.py main.py api.py scrapers\*.py
```

## Running

- Run scrapers (one-shot run):

```powershell
python main.py --no-verify --no-hn
```

- Run the API for n8n to consume (FastAPI / uvicorn):

```powershell
pip install uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

If your API is running locally and you want n8n hosted externally to reach it, expose it with a tunnel (ngrok or similar) or deploy the API to a service (Railway, Heroku, VPS, etc.).

## API Endpoints (for n8n)

- `GET /jobs/unsynced?hours=24`
  - Returns a JSON array of unsynced jobs from the last `hours` specified (default 24).
  - Each job record includes at least: `ID`, `Source`, `Title`, `Company`, `Location`, `Remote`, `Salary`, `Category`, `Description`, `URL`, `Date Posted`, `Date Found`.

- `POST /jobs/mark_synced`
  - Body (JSON): expected format is `{"ids": [<ID1>, <ID2>, ...]}`. The n8n node in the supplied workflow was configured to send `{"ids":[ <ID> ]}` per appended item; if you batch append multiple rows, prefer sending a list of IDs.

## n8n Workflow (import)

- Import `Job Scraper - Multi Sheet Export.json` into n8n (Workflows → Import).
- Edit the `HTTP Request` node to point at your deployed API URL: e.g. `https://<your-host>/jobs/unsynced?hours=24`.
- The workflow contains IF nodes that route jobs to these sheets (sheet names must match):
  - `Web Development` (sheet/tab)
  - `Web Design`
  - `Data Science & Analytics`
  - `Graphics & UI/UX`
  - `Virtual Assistant`
  - `Cybersecurity`
  - `Digital Marketing` (fallback)
  - `Internship`
  - `Caregiver/Health Care Assistant`

- Each Google Sheets node is configured to `append` rows and auto-map input fields. Confirm the column schema in each Google Sheets node matches headers in your sheet.

- After an append, the workflow calls `POST /jobs/mark_synced` (the `Mark Synced` HTTP node). Verify that node's body format matches what your API expects. Example body (n8n JSON parameters enabled):

```json
{"ids": [ {{ $json["ID"] }} ] }
```

If you append multiple rows at once, ensure the `Mark Synced` node receives all appended IDs; adjust the node to aggregate IDs into an array.

## Testing the flow manually

- Fetch unsynced jobs (test):

```bash
curl 'http://localhost:8000/jobs/unsynced?hours=24'
```

- Post mark-synced (test):

```bash
curl -X POST 'http://localhost:8000/jobs/mark_synced' -H 'Content-Type: application/json' -d '{"ids":[1,2,3]}'
```

## Mapping & Columns

The n8n workflow's Google Sheets nodes use `autoMapInputData`. The recommended column headers (order not strict) are:

- ID, Source, Title, Company, Location, Salary, Remote, Tech Stack, Score, Date Posted, Date Found, URL, Verified, Description, Category

Make sure each sheet tab uses the same header row so n8n can auto-map reliably.

## Troubleshooting

- No jobs returned from `GET /jobs/unsynced`:
  - Confirm the DB has rows with `synced_to_sheets = 0`. Run `python main.py --no-verify --no-hn` to populate.
  - Check `config.py` filters — the stricter they are, the fewer matches.

- n8n fails to reach API:
  - If n8n is remote, expose your API or deploy it.
  - Verify firewall and CORS settings; `uvicorn` + FastAPI handles CORS if configured in `api.py`.

- Mark Synced not marking rows:
  - Check the `POST /jobs/mark_synced` body format expected by your API. Adjust the `Mark Synced` node in the workflow to send `{"ids": [<ID(s)>]}`.

## Security & Privacy

- Keep `data/service_account.json` private — do not commit to source control.
- If deploying the API, secure it behind authentication or at least IP/host restrictions if sensitive.

## Extending the system

- Add new scrapers under `scrapers/` with the same return structure (dict keys listed above). Call them from `main.py`.
- Add new categories by updating `api.py`'s `CATEGORY_RULES` and the n8n workflow IF nodes and Google Sheets tabs.
- To change scheduling: use OS scheduler, a workflow runner, or host the scrapers in a serverless scheduler.

## How to contribute

- Fork, create a feature branch, and submit a PR.
- Keep scrapers focused: prefer official RSS/JSON APIs where available. Avoid scraping sites that disallow automation.
