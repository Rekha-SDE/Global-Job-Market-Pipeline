"""
Database connection helper.

Reads the settings from the .env file in the project's main folder:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
and returns a SQLAlchemy "engine" (the object that talks to PostgreSQL).

The password stays in .env, which is never uploaded to GitHub.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_SETTINGS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def get_engine():
    """Create and return the SQLAlchemy engine for our PostgreSQL database."""
    load_dotenv(PROJECT_ROOT / ".env")

    # Advanced option: a full DATABASE_URL overrides the separate settings.
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    missing = [name for name in REQUIRED_SETTINGS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing settings in .env: {', '.join(missing)}")

    # URL.create() safely handles special characters in the password.
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)