"""
Step 4 of the pipeline: the API.

A small web server (FastAPI) that reads the "jobs" table from PostgreSQL and
gives the data to the dashboard as JSON.

How to start it (from the project's main folder, with the venv active):
    uvicorn src.api.main:app --reload

Then open  http://127.0.0.1:8000/docs  in the browser to try every endpoint.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import re

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.database.connection import get_engine

app = FastAPI(title="Global Job Market Intelligence API", version="0.1.0")

# CORS: lets the dashboard (running on Live Server, port 5500) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

JOB_COLUMNS = (
    "job_id, title, company, country, city, work_mode, job_type, "
    "skills, url, posted_at, latitude, longitude"
)

_engine = None

SESSION_DAYS = 30
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


def ensure_auth_tables():
    """Create account tables so auth works before the jobs pipeline is run."""
    with get_db_engine().begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGSERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions (user_id)"
        ))


def password_hash(password, salt=None):
    """Hash a password using scrypt with a unique random salt."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return f"scrypt${salt.hex()}${digest.hex()}"


def password_matches(password, stored):
    try:
        algorithm, salt_hex, digest_hex = stored.split("$", 2)
        if algorithm != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
            n=2**14, r=8, p=1, dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_session(connection, user):
    token = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(days=SESSION_DAYS)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    connection.execute(text(
        "INSERT INTO auth_sessions (token_hash, user_id, expires_at) "
        "VALUES (:token_hash, :user_id, :expires_at)"
    ), {"token_hash": token_hash, "user_id": user["user_id"], "expires_at": expires_at})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user["user_id"], "name": user["full_name"], "email": user["email"],
    }}


def require_user(authorization):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with get_db_engine().begin() as connection:
        user = connection.execute(text("""
            SELECT u.user_id, u.full_name, u.email
            FROM auth_sessions s JOIN users u ON u.user_id = s.user_id
            WHERE s.token_hash = :token_hash AND s.expires_at > :now
        """), {"token_hash": token_hash, "now": utc_now()}).mappings().first()
        if user is None:
            raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
    return dict(user)


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


@app.post("/auth/register")
def register(payload: RegisterRequest):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Please enter your full name.")
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    ensure_auth_tables()
    with get_db_engine().begin() as connection:
        result = connection.execute(text("""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (:name, :email, :password_hash)
            ON CONFLICT (email) DO NOTHING
            RETURNING user_id, full_name, email
        """), {"name": name, "email": email,
               "password_hash": password_hash(payload.password)}).mappings().first()
        if result is None:
            raise HTTPException(status_code=409, detail="An account with this email already exists. Sign in instead.")
        return create_session(connection, dict(result))


@app.post("/auth/login")
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    ensure_auth_tables()
    with get_db_engine().begin() as connection:
        user = connection.execute(text(
            "SELECT user_id, full_name, email, password_hash FROM users WHERE email = :email"
        ), {"email": email}).mappings().first()
        if user is None or not password_matches(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        return create_session(connection, dict(user))


@app.get("/auth/me")
def current_user(authorization: str = Header(default="")):
    ensure_auth_tables()
    user = require_user(authorization)
    return {"id": user["user_id"], "name": user["full_name"], "email": user["email"]}


@app.post("/auth/logout")
def logout(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return {"status": "ok"}
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ensure_auth_tables()
    with get_db_engine().begin() as connection:
        connection.execute(text("DELETE FROM auth_sessions WHERE token_hash = :token_hash"),
                           {"token_hash": token_hash})
    return {"status": "ok"}


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
def map_markers(
    jobs: bool = True,
    internships: bool = True,
    work_mode: str | None = None,
    job_type: str | None = None,
):
    """One marker per country: position and number of jobs (for the world map).

    jobs=false      -> leave out normal jobs
    internships=false -> leave out internships
    """
    kind = job_kind_condition(jobs, internships)
    if kind is None:
        return []

    conditions = ["latitude IS NOT NULL", "longitude IS NOT NULL"]
    params = {}
    if kind:
        conditions.append(kind)
    if work_mode:
        conditions.append("work_mode = :work_mode")
        params["work_mode"] = work_mode
    if job_type:
        conditions.append("job_type = :job_type")
        params["job_type"] = job_type

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
    return run_query(sql, params)


@app.get("/company-markers")
def company_markers(
    min_lat: float = -90,
    max_lat: float = 90,
    min_lng: float = -180,
    max_lng: float = 180,
    limit: int = 60,
    jobs: bool = True,
    internships: bool = True,
    country: str | None = None,
    work_mode: str | None = None,
    job_type: str | None = None,
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
    if country:
        conditions.append("country = :country")
    if work_mode:
        conditions.append("work_mode = :work_mode")
    if job_type:
        conditions.append("job_type = :job_type")
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
    if country:
        params["country"] = country
    if work_mode:
        params["work_mode"] = work_mode
    if job_type:
        params["job_type"] = job_type
    return run_query(sql, params)
