"""
Step 4 of the pipeline: the API.

A small web server (FastAPI) that reads the "jobs" table from PostgreSQL and
gives the data to the dashboard as JSON.

How to start it (from the project's main folder, with the venv active):
    uvicorn src.api.main:app --reload

Then open  http://127.0.0.1:8000/docs  in the browser to try every endpoint.
"""

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.database.connection import get_engine

app = FastAPI(title="Global Job Market Intelligence API", version="0.1.0")

# CORS: lets the dashboard (running on Live Server, port 5500) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

JOB_COLUMNS = (
    "job_id, title, company, country, city, work_mode, job_type, "
    "skills, url, posted_at, latitude, longitude"
)

_engine = None


def get_db_engine():
    """Create the database engine once and reuse it."""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def run_query(sql, params=None):
    """Run a SELECT query and return the rows as a list of dictionaries."""
    with get_db_engine().connect() as connection:
        rows = connection.execute(text(sql), params or {}).mappings().all()
    return [dict(row) for row in rows]


def utc_now():
    """Current time in UTC without timezone info (same style as the database)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def build_jobs_query(country, job_type, work_mode, search, limit, offset, company=None, city=None):
    """Build the SQL text and parameters for /jobs.

    Only the filters the user sent are added. Values always go in as parameters
    (never pasted into the SQL text), which protects against SQL injection.
    """
    conditions = []
    params = {"limit": max(1, min(limit, 200)), "offset": max(0, offset)}

    if country:
        conditions.append("country = :country")
        params["country"] = country
    if job_type:
        conditions.append("job_type = :job_type")
        params["job_type"] = job_type
    if work_mode:
        conditions.append("work_mode = :work_mode")
        params["work_mode"] = work_mode
    if company:
        conditions.append("company = :company")
        params["company"] = company
    if city:
        conditions.append("city = :city")
        params["city"] = city
    if search:
        conditions.append("(LOWER(title) LIKE :search OR LOWER(company) LIKE :search)")
        params["search"] = f"%{search.lower()}%"

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = (
        f"SELECT {JOB_COLUMNS} FROM jobs {where} "
        "ORDER BY posted_at DESC NULLS LAST LIMIT :limit OFFSET :offset"
    )
    return sql, params


def job_kind_condition(jobs, internships):
    """SQL for the Jobs / Internships checkboxes. Returns None when both are off."""
    if jobs and internships:
        return ""
    if jobs:
        return "(job_type IS NULL OR job_type <> 'Internship')"
    if internships:
        return "job_type = 'Internship'"
    return None


@app.get("/health")
def health():
    """Quick check that the API and the database work."""
    total = run_query("SELECT COUNT(*) AS total FROM jobs")[0]["total"]
    return {"status": "ok", "jobs_in_database": total}


@app.get("/jobs")
def list_jobs(
    country: str | None = None,
    job_type: str | None = None,
    work_mode: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    company: str | None = None,
    city: str | None = None,
):
    """List jobs, newest first. Filters: country, city, company, job_type, work_mode, search."""
    sql, params = build_jobs_query(country, job_type, work_mode, search, limit, offset, company, city)
    return run_query(sql, params)


@app.get("/stats")
def stats():
    """Numbers for the four cards on the dashboard."""
    now = utc_now()
    sql = """
        SELECT
            COUNT(*) AS total_jobs,
            SUM(CASE WHEN posted_at >= :day THEN 1 ELSE 0 END) AS new_today,
            SUM(CASE WHEN posted_at >= :week THEN 1 ELSE 0 END) AS new_this_week,
            SUM(CASE WHEN job_type = 'Internship' THEN 1 ELSE 0 END) AS internships,
            COUNT(DISTINCT company) AS companies,
            COUNT(DISTINCT CASE WHEN country NOT IN ('Unknown', 'Remote') THEN country END) AS countries
        FROM jobs
    """
    row = run_query(sql, {"day": now - timedelta(days=1), "week": now - timedelta(days=7)})[0]
    # SUM() gives NULL on an empty table, so replace it with 0.
    return {key: (value or 0) for key, value in row.items()}


@app.get("/companies")
def top_companies(limit: int = 10, country: str | None = None):
    """Companies with the most open jobs (optionally only in one country)."""
    params = {"limit": max(1, min(limit, 50))}
    where = ""
    if country:
        where = "WHERE country = :country"
        params["country"] = country
    sql = (
        f"SELECT company, COUNT(*) AS openings FROM jobs {where} "
        "GROUP BY company ORDER BY openings DESC, company LIMIT :limit"
    )
    return run_query(sql, params)


@app.get("/map-markers")
def map_markers(jobs: bool = True, internships: bool = True):
    """One marker per country: position and number of jobs (for the world map).

    jobs=false      -> leave out normal jobs
    internships=false -> leave out internships
    """
    kind = job_kind_condition(jobs, internships)
    if kind is None:
        return []

    conditions = ["latitude IS NOT NULL", "longitude IS NOT NULL"]
    if kind:
        conditions.append(kind)

    sql = f"""
        SELECT
            country,
            AVG(latitude) AS latitude,
            AVG(longitude) AS longitude,
            COUNT(*) AS jobs,
            SUM(CASE WHEN job_type = 'Internship' THEN 1 ELSE 0 END) AS internships
        FROM jobs
        WHERE {' AND '.join(conditions)}
        GROUP BY country
        ORDER BY jobs DESC
    """
    return run_query(sql)


@app.get("/company-markers")
def company_markers(
    min_lat: float = -90,
    max_lat: float = 90,
    min_lng: float = -180,
    max_lng: float = 180,
    limit: int = 60,
    jobs: bool = True,
    internships: bool = True,
):
    """Companies that hire in a city, inside the part of the map you are looking at.

    One row per company + city, with the number of open jobs. The biggest come first.
    Only jobs with an exact city position are included.
    """
    kind = job_kind_condition(jobs, internships)
    if kind is None:
        return []

    conditions = [
        "location_precision = 'city'",
        "latitude BETWEEN :min_lat AND :max_lat",
        "longitude BETWEEN :min_lng AND :max_lng",
    ]
    if kind:
        conditions.append(kind)

    sql = f"""
        SELECT
            company,
            city,
            country,
            AVG(latitude) AS latitude,
            AVG(longitude) AS longitude,
            COUNT(*) AS openings,
            SUM(CASE WHEN job_type = 'Internship' THEN 1 ELSE 0 END) AS internships
        FROM jobs
        WHERE {' AND '.join(conditions)}
        GROUP BY company, city, country
        ORDER BY openings DESC, company
        LIMIT :limit
    """
    params = {
        "min_lat": min(min_lat, max_lat), "max_lat": max(min_lat, max_lat),
        "min_lng": min(min_lng, max_lng), "max_lng": max(min_lng, max_lng),
        "limit": max(1, min(limit, 200)),
    }
    return run_query(sql, params)