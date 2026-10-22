-- Step 3 of the pipeline: DATABASE.
-- Creates the table that stores the clean jobs. Safe to run many times.

CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,          -- unique id of the job (from the source)
    title       TEXT NOT NULL,
    company     TEXT NOT NULL,
    country     TEXT,
    city        TEXT,
    work_mode   TEXT,                      -- Remote / Hybrid / On-site
    job_type    TEXT,                      -- Internship / Full-time / Part-time / Contract
    skills      TEXT,
    url         TEXT NOT NULL UNIQUE,      -- the same job link can only be stored once
    posted_at   TIMESTAMP,
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    location_precision TEXT,               -- city = exact city, country = only the country, none = unknown
    source      TEXT,
    loaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes make searches by country, job type and date fast.
CREATE INDEX IF NOT EXISTS idx_jobs_country   ON jobs (country);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type  ON jobs (job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs (posted_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company_city ON jobs (company, city);

-- Accounts are used by the sign-in and registration pages.
CREATE TABLE IF NOT EXISTS users (
    user_id       BIGSERIAL PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Store only a hash of each random session token; raw tokens stay in the browser.
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions (user_id);
