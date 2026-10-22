"""
Tests for src/transformation/clean_jobs.py (cleaning the raw Arbeitnow jobs).

No internet, no database. Run from the project's main folder:   pytest
"""

import json

import pytest

from src.transformation import clean_jobs


def make_job(**changes):
    """One raw job, shaped like the Arbeitnow answer. Change fields per test."""
    job = {
        "slug": "job-1",
        "company_name": "Acme GmbH",
        "title": "Data Engineer",
        "description": "",
        "remote": False,
        "url": "https://example.com/job-1",
        "tags": ["Data", "Python"],
        "job_types": ["Full Time"],
        "location": "Berlin",
        "created_at": 1760000000,
    }
    job.update(changes)
    return job


# ---------------------------------------------------------------------------
# job type
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "title, job_types, expected",
    [
        ("Software Intern", ["Full Time"], "Internship"),
        ("Praktikum Marketing", [], "Internship"),
        ("Data Engineer", ["Internship"], "Internship"),
        ("Werkstudent Controlling", ["Student"], "Part-time"),
        ("Sales Assistant (Teilzeit)", [], "Part-time"),
        ("Freelance Designer", [], "Contract"),
        ("Backend Developer", ["Full Time"], "Full-time"),
        ("Backend Developer", None, "Full-time"),
    ],
)
def test_detect_job_type(title, job_types, expected):
    assert clean_jobs.detect_job_type(title, job_types) == expected


# ---------------------------------------------------------------------------
# work mode
# ---------------------------------------------------------------------------
def test_detect_work_mode():
    assert clean_jobs.detect_work_mode(True, "Developer", "") == "Remote"
    assert clean_jobs.detect_work_mode(False, "Developer", "We offer a hybrid model") == "Hybrid"
    assert clean_jobs.detect_work_mode(False, "Hybrid Developer", "") == "Hybrid"
    assert clean_jobs.detect_work_mode(False, "Developer", "Office in Berlin") == "On-site"
    assert clean_jobs.detect_work_mode(None, "Developer", None) == "On-site"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def test_convert_timestamp():
    assert clean_jobs.convert_timestamp(0) == "1970-01-01 00:00:00"
    assert clean_jobs.convert_timestamp(1760000000) == "2025-10-09 08:53:20"
    assert clean_jobs.convert_timestamp(None) is None
    assert clean_jobs.convert_timestamp("not a number") is None


def test_join_tags():
    assert clean_jobs.join_tags(["Python", " SQL ", ""]) == "Python, SQL"
    assert clean_jobs.join_tags([]) == ""
    assert clean_jobs.join_tags(None) == ""


# ---------------------------------------------------------------------------
# clean_jobs (the main cleaning function)
# ---------------------------------------------------------------------------
def test_clean_jobs_has_the_expected_columns_and_values():
    result = clean_jobs.clean_jobs([make_job()])

    assert list(result.columns) == clean_jobs.COLUMNS
    row = result.iloc[0]
    assert row["job_id"] == "job-1"
    assert row["company"] == "Acme GmbH"
    assert row["country"] == "Germany"
    assert row["city"] == "Berlin"
    assert row["work_mode"] == "On-site"
    assert row["job_type"] == "Full-time"
    assert row["skills"] == "Data, Python"
    assert row["posted_at"] == "2025-10-09 08:53:20"
    assert row["location_precision"] == "country"   # the city lookup comes later
    assert row["source"] == "arbeitnow"


def test_clean_jobs_removes_jobs_without_title_or_company():
    jobs = [
        make_job(slug="ok"),
        make_job(slug="no-title", title="", url="https://example.com/2"),
        make_job(slug="no-company", company_name=None, url="https://example.com/3"),
    ]
    result = clean_jobs.clean_jobs(jobs)
    assert list(result["job_id"]) == ["ok"]


def test_clean_jobs_removes_duplicates_by_job_id_and_by_url():
    jobs = [
        make_job(slug="a", url="https://example.com/a"),
        make_job(slug="a", url="https://example.com/a-copy"),    # same job_id
        make_job(slug="b", url="https://example.com/a"),         # same url
        make_job(slug="c", url="https://example.com/c"),
    ]
    result = clean_jobs.clean_jobs(jobs)
    assert list(result["job_id"]) == ["a", "c"]


def test_clean_jobs_handles_messy_values_without_crashing():
    messy = make_job(slug="messy", url="https://example.com/m", tags=None, job_types=None,
                     location=None, created_at="bad", remote=None, description=None)
    row = clean_jobs.clean_jobs([messy]).iloc[0]

    assert row["country"] == "Unknown"
    assert row["location_precision"] == "none"
    assert row["skills"] == ""
    assert row["posted_at"] is None


def test_clean_jobs_with_no_jobs_gives_an_empty_table_with_columns():
    result = clean_jobs.clean_jobs([])
    assert len(result) == 0
    assert list(result.columns) == clean_jobs.COLUMNS


# ---------------------------------------------------------------------------
# reading the raw files
# ---------------------------------------------------------------------------
def test_load_raw_jobs_joins_all_pages(tmp_path):
    raw_file = tmp_path / "arbeitnow_20260101_000000.json"
    raw_file.write_text(
        json.dumps({"pages": [{"data": [make_job(slug="a")]},
                              {"data": [make_job(slug="b"), make_job(slug="c")]}]}),
        encoding="utf-8",
    )
    jobs = clean_jobs.load_raw_jobs(raw_file)
    assert [job["slug"] for job in jobs] == ["a", "b", "c"]


def test_find_latest_raw_file_picks_the_newest(tmp_path, monkeypatch):
    for name in ["arbeitnow_20260101_000000.json", "arbeitnow_20261019_093737.json",
                 "arbeitnow_20260601_120000.json"]:
        (tmp_path / name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(clean_jobs, "RAW_DATA_DIR", tmp_path)

    assert clean_jobs.find_latest_raw_file().name == "arbeitnow_20261019_093737.json"


def test_find_latest_raw_file_without_files_gives_none(tmp_path, monkeypatch):
    monkeypatch.setattr(clean_jobs, "RAW_DATA_DIR", tmp_path)
    assert clean_jobs.find_latest_raw_file() is None