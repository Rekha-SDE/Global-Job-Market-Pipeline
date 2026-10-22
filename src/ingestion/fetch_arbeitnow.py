"""
Step 1 of the pipeline: INGESTION.

This script downloads job postings from the free Arbeitnow API
(no API key needed) and saves the raw answer to a JSON file in data/raw.

How to run (from the project's main folder, with the venv active):
    python src/ingestion/fetch_arbeitnow.py
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

API_URL = "https://www.arbeitnow.com/api/job-board-api"
PAGES_TO_FETCH = 5          # how many pages of jobs to download
PAUSE_SECONDS = 1           # wait between requests, to be polite to the API
TIMEOUT = (5, 20)           # (seconds to connect, seconds to wait for the answer)
MAX_ATTEMPTS = 3            # try each page up to 3 times before giving up
RETRY_WAIT_SECONDS = 2      # wait between those attempts

# The project's main folder is two levels above this file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def fetch_page(session, page_number):
    """Download ONE page from the API. Returns a dictionary, or None if it failed."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(
                API_URL, params={"page": page_number}, timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            logger.warning(
                "Page %s, attempt %s/%s failed: %s",
                page_number, attempt, MAX_ATTEMPTS, error,
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_WAIT_SECONDS)

    logger.error("Giving up on page %s after %s attempts.", page_number, MAX_ATTEMPTS)
    return None


def fetch_all_pages():
    """Download the first PAGES_TO_FETCH pages and return them as a list."""
    pages = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "global-job-market-pipeline/0.1 (learning project)"})

        for page_number in range(1, PAGES_TO_FETCH + 1):
            logger.info("Fetching page %s of %s ...", page_number, PAGES_TO_FETCH)
            page = fetch_page(session, page_number)

            if page is None:
                logger.error("Stopping early because page %s could not be fetched.", page_number)
                break

            jobs_on_page = page.get("data", [])
            logger.info("Page %s returned %s jobs.", page_number, len(jobs_on_page))

            if not jobs_on_page:
                logger.info("No jobs on page %s, so there are no more pages.", page_number)
                break

            pages.append(page)  # keep the raw answer exactly as received

            if page_number < PAGES_TO_FETCH:
                time.sleep(PAUSE_SECONDS)

    return pages


def save_raw_file(pages):
    """Save the downloaded pages into data/raw/arbeitnow_YYYYMMDD_HHMMSS.json."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    file_path = RAW_DATA_DIR / f"arbeitnow_{now:%Y%m%d_%H%M%S}.json"

    content = {
        "source": API_URL,
        "fetched_at": now.isoformat(timespec="seconds"),
        "pages": pages,
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(content, file, ensure_ascii=False, indent=2)

    return file_path


def main():
    logger.info("Starting Arbeitnow ingestion.")
    pages = fetch_all_pages()

    if not pages:
        logger.error("Nothing was downloaded, so no file was saved.")
        return 1

    total_jobs = sum(len(page.get("data", [])) for page in pages)
    file_path = save_raw_file(pages)

    logger.info("Done. Saved %s jobs from %s pages.", total_jobs, len(pages))
    logger.info("File: %s", file_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())