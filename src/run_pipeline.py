"""
The whole pipeline in ONE command.

    1. Fetch    download new jobs from the Arbeitnow API   -> data/raw
    2. Clean    clean them with pandas, find city positions -> data/processed
    3. Load     save them in the PostgreSQL table "jobs"

How to run (from the project's main folder, with the venv active):
    python src/run_pipeline.py

Options:
    --skip-fetch      do not download again; use the newest file already in data/raw
    --no-geocoding    skip the online city lookup (faster, but less exact map positions)

If a step fails, the pipeline stops (the next steps need the result of the failed one).
Every run is also written to logs/pipeline.log, which helps when it runs on a schedule.
"""

import logging
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:      # lets "python src/run_pipeline.py" find the src package
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import load_jobs                  # noqa: E402
from src.ingestion import fetch_arbeitnow           # noqa: E402
from src.transformation import clean_jobs           # noqa: E402

LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"
logger = logging.getLogger("pipeline")


def build_steps(skip_fetch=False, skip_geocoding=False):
    """The steps in order. Each step is (name, function). A function returns 0 when it worked."""
    steps = []
    if not skip_fetch:
        steps.append(("Fetch jobs from Arbeitnow", lambda: fetch_arbeitnow.main()))
    clean_options = ["--no-geocoding"] if skip_geocoding else []
    steps.append(("Clean the jobs", lambda: clean_jobs.main(clean_options)))
    steps.append(("Load the jobs into PostgreSQL", lambda: load_jobs.main()))
    return steps


def run_steps(steps):
    """Run the steps one by one. Stops at the first failure. Returns 0 (ok) or 1 (failed)."""
    started = time.time()
    results = []   # (name, seconds, ok)

    for number, (name, step) in enumerate(steps, start=1):
        logger.info("=== Step %s of %s: %s ===", number, len(steps), name)
        step_started = time.time()
        try:
            ok = step() in (0, None)
        except Exception:                       # a crash inside the step
            logger.error("Step crashed:\n%s", traceback.format_exc())
            ok = False
        results.append((name, time.time() - step_started, ok))
        if not ok:
            logger.error("Step %s FAILED: %s. Stopping the pipeline.", number, name)
            break

    logger.info("--- Summary ---")
    for name, seconds, ok in results:
        logger.info("%-34s %6.1f s   %s", name, seconds, "OK" if ok else "FAILED")
    skipped = len(steps) - len(results)
    if skipped:
        logger.info("%s later step(s) were not run.", skipped)

    success = all(ok for _, _, ok in results) and skipped == 0
    logger.info("Pipeline %s in %.1f s.", "finished successfully" if success else "FAILED",
                time.time() - started)
    return 0 if success else 1


def setup_file_logging():
    """Also write the messages into logs/pipeline.log (the folder is created if needed)."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                                           datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(handler)
    return handler


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    handler = setup_file_logging()
    try:
        steps = build_steps(skip_fetch="--skip-fetch" in args,
                            skip_geocoding="--no-geocoding" in args)
        return run_steps(steps)
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    sys.exit(main())