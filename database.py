# ─────────────────────────────────────────────────────────────
# database.py  —  SQLite handler for storing & deduplicating jobs
# ─────────────────────────────────────────────────────────────

import sqlite3
import hashlib
from datetime import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def init_db():
    """Create tables if they don't exist yet."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,   -- MD5 hash of URL
            source      TEXT NOT NULL,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            salary      TEXT,
            remote      TEXT,
            description TEXT,
            url         TEXT,
            date_posted TEXT,
            date_found  TEXT NOT NULL,

            -- AI fields (populated in Phase 2)
            verified    INTEGER DEFAULT NULL,  -- 1=true, 0=false
            scam_flag   TEXT    DEFAULT NULL,
            quality_score INTEGER DEFAULT NULL,
            tech_stack  TEXT    DEFAULT NULL,  -- stored as comma-separated

            -- Tracking
            still_active INTEGER DEFAULT 1,   -- 1=active, 0=expired
            last_checked TEXT    DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS scrape_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at      TEXT NOT NULL,
            source      TEXT NOT NULL,
            jobs_found  INTEGER DEFAULT 0,
            jobs_new    INTEGER DEFAULT 0,
            error       TEXT DEFAULT NULL
        );
    """)
    conn.commit()
    conn.close()
    print("  ✓ Database ready")


def url_to_id(url: str) -> str:
    """Convert a URL to a short unique ID."""
    return hashlib.md5(url.strip().encode()).hexdigest()[:16]


def is_duplicate(job_id: str) -> bool:
    """Return True if this job is already in the database."""
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return row is not None


def insert_job(job: dict) -> bool:
    """
    Insert a job. Returns True if inserted, False if duplicate.
    job dict keys: source, title, company, location, salary,
                   remote, description, url, date_posted
    """
    job_id = url_to_id(job.get("url", ""))
    if is_duplicate(job_id):
        return False

    conn = get_connection()
    conn.execute("""
        INSERT INTO jobs (
            id, source, title, company, location, salary,
            remote, description, url, date_posted, date_found
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        job.get("source", ""),
        job.get("title", "")[:200],
        job.get("company", "")[:100],
        job.get("location", "")[:100],
        job.get("salary", "")[:100],
        job.get("remote", ""),
        job.get("description", "")[:1000],
        job.get("url", ""),
        job.get("date_posted", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ))
    conn.commit()
    conn.close()
    return True


def log_run(source: str, found: int, new: int, error: str = None):
    """Record metadata about each scrape run."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO scrape_runs (run_at, source, jobs_found, jobs_new, error)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M"), source, found, new, error))
    conn.commit()
    conn.close()


def get_all_jobs(limit: int = None) -> list:
    """Fetch all jobs, newest first."""
    conn = get_connection()
    query = "SELECT * FROM jobs ORDER BY date_found DESC"
    if limit:
        query += f" LIMIT {limit}"
    rows = [dict(r) for r in conn.execute(query).fetchall()]
    conn.close()
    return rows


def get_stats() -> dict:
    """Return summary stats."""
    conn = get_connection()
    stats = {}
    stats["total"]   = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    stats["remote"]  = conn.execute("SELECT COUNT(*) FROM jobs WHERE remote='Yes'").fetchone()[0]
    stats["sources"] = dict(conn.execute(
        "SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY COUNT(*) DESC"
    ).fetchall())
    stats["today"]   = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE date_found LIKE ?",
        (datetime.now().strftime("%Y-%m-%d") + "%",)
    ).fetchone()[0]
    conn.close()
    return stats
