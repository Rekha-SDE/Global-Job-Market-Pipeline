"""
Tests for the SQL building helpers in src/api/main.py.

These only build text and parameters: no database and no web server are used.
Run from the project's main folder:   pytest
"""

from src.api.main import build_jobs_query, job_kind_condition


def test_jobs_query_without_filters_has_no_where():
    sql, params = build_jobs_query(None, None, None, None, 50, 0)

    assert "WHERE" not in sql
    assert params == {"limit": 50, "offset": 0}


def test_jobs_query_adds_only_the_filters_that_are_given():
    sql, params = build_jobs_query("Germany", None, "Remote", None, 50, 0, company="Acme", city="Berlin")

    assert "country = :country" in sql
    assert "work_mode = :work_mode" in sql
    assert "company = :company" in sql
    assert "city = :city" in sql
    assert "job_type = :job_type" not in sql      # (job_type is in the SELECT list, but not filtered)
    assert params["country"] == "Germany" and params["city"] == "Berlin"


def test_jobs_query_never_puts_user_text_into_the_sql():
    evil = "x' OR '1'='1"
    sql, params = build_jobs_query(evil, None, None, evil, 50, 0, company=evil, city=evil)

    assert evil not in sql            # the text travels as a parameter, not inside the SQL
    assert "OR '1'='1" not in sql
    assert params["country"] == evil


def test_search_is_case_insensitive_and_uses_wildcards():
    sql, params = build_jobs_query(None, None, None, "Data", 50, 0)

    assert "LOWER(title) LIKE :search" in sql
    assert params["search"] == "%data%"


def test_limit_and_offset_are_kept_in_a_safe_range():
    _, params = build_jobs_query(None, None, None, None, 100000, -5)
    assert params["limit"] == 200 and params["offset"] == 0

    _, params = build_jobs_query(None, None, None, None, 0, 0)
    assert params["limit"] == 1


def test_job_kind_condition_for_the_two_checkboxes():
    assert job_kind_condition(True, True) == ""                       # no extra filter
    assert "<> 'Internship'" in job_kind_condition(True, False)       # only normal jobs
    assert job_kind_condition(False, True) == "job_type = 'Internship'"
    assert job_kind_condition(False, False) is None                   # both off: nothing to show