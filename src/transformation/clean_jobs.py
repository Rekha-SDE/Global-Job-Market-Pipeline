"""
Step 2 of the pipeline: TRANSFORMATION.

Reads the newest raw file from data/raw (made by src/ingestion/fetch_arbeitnow.py),
cleans it with pandas and writes data/processed/jobs_clean.csv.

How to run (from the project's main folder, with the venv active):
    python src/transformation/clean_jobs.py
    python src/transformation/clean_jobs.py --no-geocoding     (skip the online city lookup)
"""

import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# These imports work both when you run the file directly and when pytest imports it.
try:
    from src.transformation.geo import (
        add_city_coordinates, coordinates_for, normalize, split_location,
    )
except ImportError:
    from geo import add_city_coordinates, coordinates_for, normalize, split_location

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DATA_DIR / "jobs_clean.csv"

# The columns of the clean file, in this order.
COLUMNS = [
    "job_id", "title", "company", "country", "city", "work_mode", "job_type",
    "skills", "url", "posted_at", "latitude", "longitude", "location_precision", "source",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Read the raw data
# ---------------------------------------------------------------------------
def find_latest_raw_file():
    """Return the newest data/raw/arbeitnow_*.json file, or None."""
    files = sorted(RAW_DATA_DIR.glob("arbeitnow_*.json"))
    return files[-1] if files else None


def load_raw_jobs(file_path):
    """Read the raw file and return ONE flat list with all jobs from all pages."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = json.load(file)

    jobs = []
    for page in content.get("pages", []):
        jobs.extend(page.get("data", []))
    return jobs


# ---------------------------------------------------------------------------
# 2. Small helper functions (easy to test one by one)
# ---------------------------------------------------------------------------
def detect_job_type(title, job_types):
    """Return Internship, Part-time, Contract or Full-time."""
    # job_types is a list like ["Full Time"]; join it into one lowercase text.
    types_text = " ".join(job_types) if isinstance(job_types, list) else str(job_types or "")
    text = normalize(f"{title} {types_text}")

    if any(word in text for word in ("intern", "praktikum", "praktikant", "trainee")):
        return "Internship"
    if any(word in text for word in ("part time", "part-time", "teilzeit", "werkstudent",
                                      "working student")):
        return "Part-time"
    if any(word in text for word in ("contract", "freelance", "freiberuf", "temporary")):
        return "Contract"
    return "Full-time"


def detect_work_mode(is_remote, title, description):
    """Return Remote, Hybrid or On-site."""
    if is_remote is True:
        return "Remote"
    text = normalize(f"{title} {description}")
    if "hybrid" in text:
        return "Hybrid"
    return "On-site"


def convert_timestamp(value):
    """Arbeitnow gives 'created_at' as seconds since 1970. Return an ISO date text."""
    try:
        moment = datetime.fromtimestamp(int(value), tz=timezone.utc)
        return moment.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return None


def join_tags(tags):
    """['Python', 'SQL'] -> 'Python, SQL'."""
    if isinstance(tags, list):
        return ", ".join(str(tag).strip() for tag in tags if str(tag).strip())
    return str(tags or "").strip()


# ---------------------------------------------------------------------------
# 3. Clean everything
# ---------------------------------------------------------------------------
def clean_jobs(raw_jobs):
    """Turn the list of raw jobs into a clean pandas DataFrame."""
    rows = []
    for job in raw_jobs:
        title = str(job.get("title") or "").strip()
        company = str(job.get("company_name") or "").strip()
        if not title or not company:
            continue  # a job without a title or company is useless

        url = str(job.get("url") or "").strip()
        job_id = str(job.get("slug") or url).strip()
        if not job_id:
            continue

        city, country = split_location(job.get("location"))
        latitude, longitude = coordinates_for(country)

        rows.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "country": country,
            "city": city,
            "work_mode": detect_work_mode(job.get("remote"), title, job.get("description", "")),
            "job_type": detect_job_type(title, job.get("job_types")),
            "skills": join_tags(job.get("tags")),
            "url": url,
            "posted_at": convert_timestamp(job.get("created_at")),
            "latitude": latitude,
            "longitude": longitude,
            # country = only the country is known, none = no position at all.
            # (add_city_coordinates() later upgrades jobs to "city".)
            "location_precision": "country" if latitude is not None else "none",
            "source": "arbeitnow",
        })

    dataframe = pd.DataFrame(rows, columns=COLUMNS)

    # The same job can appear on two pages: keep only the first copy.
    dataframe = dataframe.drop_duplicates(subset="job_id")
    dataframe = dataframe[dataframe["url"] != ""].drop_duplicates(subset="url")
    return dataframe.reset_index(drop=True)


def log_summary(dataframe, raw_count):
    """Print a short report, so you can see if the cleaning looks right."""
    logger.info("Raw jobs: %s | Clean jobs: %s | Removed: %s",
                raw_count, len(dataframe), raw_count - len(dataframe))
    logger.info("Job types: %s", dataframe["job_type"].value_counts().to_dict())
    logger.info("Work modes: %s", dataframe["work_mode"].value_counts().to_dict())
    logger.info("Top countries: %s", dataframe["country"].value_counts().head(8).to_dict())
    logger.info("Location precision: %s", dataframe["location_precision"].value_counts().to_dict())

    unknown = dataframe[dataframe["country"] == "Unknown"]
    if len(unknown):
        common = Counter(unknown["city"].fillna("(empty)")).most_common(10)
        logger.info("%s jobs have an unknown country. Most common locations: %s",
                    len(unknown), common)
        logger.info("Tip: add these cities to src/transformation/geo.py to improve the map.")


def main(argv=None):
    skip_geocoding = "--no-geocoding" in (sys.argv[1:] if argv is None else argv)
    raw_file = find_latest_raw_file()
    if raw_file is None:
        logger.error("No raw file found in %s. Run fetch_arbeitnow.py first.", RAW_DATA_DIR)
        return 1

    logger.info("Reading %s", raw_file.name)
    raw_jobs = load_raw_jobs(raw_file)
    dataframe = clean_jobs(raw_jobs)

    if skip_geocoding:
        logger.info("Skipping the city lookup (--no-geocoding).")
    else:
        # Finds the coordinates of every city (free service, cached in data/processed).
        dataframe = add_city_coordinates(dataframe)
    log_summary(dataframe, len(raw_jobs))

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    # utf-8-sig lets Excel show accents (a, o, u with dots) correctly.
    dataframe.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    logger.info("Saved %s rows to %s", len(dataframe), OUTPUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())