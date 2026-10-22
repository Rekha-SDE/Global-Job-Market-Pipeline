"""
Step 3 of the pipeline: LOAD into the database.

Reads data/processed/jobs_clean.csv and saves the jobs into the PostgreSQL table "jobs".
Running it again is safe: jobs that are already in the table are updated (no duplicates).

How to run (from the project's main folder, with the venv active):
    python src/database/load_jobs.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# These imports work both when you run the file directly and when pytest imports it.
try:
    from src.database.connection import get_engine
except ImportError:
    from connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = PROJECT_ROOT / "data" / "processed" / "jobs_clean.csv"
SQL_FILE = PROJECT_ROOT / "sql" / "001_create_tables.sql"
CHUNK_SIZE = 500   # how many rows are sent to the database at once

COLUMNS = [
    "job_id", "title", "company", "country", "city", "work_mode", "job_type",
    "skills", "url", "posted_at", "latitude", "longitude", "location_precision", "source",
]

# New job -> inserted.  Job that already exists (same job_id) -> its values are UPDATED,
# so better data (for example new city coordinates) replaces the old values.
UPDATE_COLUMNS = [name for name in COLUMNS if name != "job_id"]
INSERT_SQL = text(
    "INSERT INTO jobs (" + ", ".join(COLUMNS) + ") "
    "VALUES (" + ", ".join(f":{name}" for name in COLUMNS) + ") "
    "ON CONFLICT (job_id) DO UPDATE SET "
    + ", ".join(f"{name} = EXCLUDED.{name}" for name in UPDATE_COLUMNS)
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_tables(connection):
    """Run the SQL file that creates the table (if it does not exist yet)."""
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    # Remove "-- comment" lines, then run each statement one by one.
    lines = [line for line in sql_text.splitlines() if not line.strip().startswith("--")]
    for statement in "\n".join(lines).split(";"):
        if statement.strip():
            connection.execute(text(statement))


def ensure_columns(connection):
    """Tables made by an older version of this project may miss newer columns: add them."""
    existing = {column["name"] for column in inspect(connection).get_columns("jobs")}
    if "location_precision" not in existing:
        connection.execute(text("ALTER TABLE jobs ADD COLUMN location_precision TEXT"))
        logger.info("Added the new column 'location_precision' to the table 'jobs'.")


def read_clean_csv():
    """Read the clean CSV and turn empty values into None (NULL in the database)."""
    dataframe = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
    if "location_precision" not in dataframe.columns:   # CSV made by an older version
        dataframe["location_precision"] = None
    # Dates become normal Python datetimes (empty ones become None).
    posted = pd.to_datetime(dataframe["posted_at"], errors="coerce")
    dataframe["posted_at"] = pd.Series(
        [value.to_pydatetime() if pd.notna(value) else None for value in posted],
        index=dataframe.index,
        dtype=object,   # keep them as plain Python datetimes
    )
    dataframe = dataframe[COLUMNS].astype(object)
    return dataframe.where(dataframe.notna(), None)


def count_jobs(connection):
    return connection.execute(text("SELECT COUNT(*) FROM jobs")).scalar()


def main():
    if not CSV_FILE.exists():
        logger.error("File not found: %s. Run clean_jobs.py first.", CSV_FILE)
        return 1

    dataframe = read_clean_csv()
    records = dataframe.to_dict(orient="records")
    logger.info("Read %s clean jobs from %s", len(records), CSV_FILE.name)

    try:
        engine = get_engine()
        # engine.begin() = one transaction: if something fails, nothing is half-saved.
        with engine.begin() as connection:
            create_tables(connection)
            ensure_columns(connection)
            before = count_jobs(connection)

            for start in range(0, len(records), CHUNK_SIZE):
                connection.execute(INSERT_SQL, records[start:start + CHUNK_SIZE])

            after = count_jobs(connection)
            top_countries = connection.execute(text(
                "SELECT country, COUNT(*) AS jobs FROM jobs "
                "GROUP BY country ORDER BY jobs DESC LIMIT 5"
            )).fetchall()
    except RuntimeError as error:
        logger.error("%s", error)
        return 1
    except SQLAlchemyError as error:
        logger.error("Database problem: %s", error)
        logger.error("Check that PostgreSQL is running and the .env settings are correct.")
        return 1

    inserted = after - before
    logger.info("Inserted %s new jobs, updated %s jobs that already existed.",
                inserted, len(records) - inserted)
    logger.info("The table 'jobs' now has %s rows.", after)
    logger.info("Top countries in the database: %s", [tuple(row) for row in top_countries])
    return 0


if __name__ == "__main__":
    sys.exit(main())