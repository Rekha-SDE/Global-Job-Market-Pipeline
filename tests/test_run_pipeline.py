"""
Tests for src/run_pipeline.py (the one-command pipeline).

The real steps (download, clean, database) are replaced by tiny fake functions,
so these tests need no internet and no database.
Run from the project's main folder:   pytest
"""

from src import run_pipeline


def test_steps_run_in_order_and_the_pipeline_succeeds():
    order = []
    steps = [
        ("one", lambda: order.append("one") or 0),
        ("two", lambda: order.append("two") or 0),
        ("three", lambda: order.append("three") or 0),
    ]
    assert run_pipeline.run_steps(steps) == 0
    assert order == ["one", "two", "three"]


def test_a_failing_step_stops_the_pipeline():
    order = []
    steps = [
        ("one", lambda: order.append("one") or 0),
        ("two", lambda: order.append("two") or 1),     # returns 1 = failed
        ("three", lambda: order.append("three") or 0),
    ]
    assert run_pipeline.run_steps(steps) == 1
    assert order == ["one", "two"]                      # step three never ran


def test_a_crashing_step_is_reported_and_stops_the_pipeline():
    order = []

    def crash():
        raise ValueError("boom")

    steps = [("one", crash), ("two", lambda: order.append("two") or 0)]
    assert run_pipeline.run_steps(steps) == 1
    assert order == []


def test_a_step_that_returns_nothing_counts_as_success():
    assert run_pipeline.run_steps([("one", lambda: None)]) == 0


def test_build_steps_default_has_three_steps_in_the_right_order():
    names = [name for name, _ in run_pipeline.build_steps()]
    assert names == ["Fetch jobs from Arbeitnow", "Clean the jobs", "Load the jobs into PostgreSQL"]


def test_skip_fetch_removes_only_the_download_step():
    names = [name for name, _ in run_pipeline.build_steps(skip_fetch=True)]
    assert names == ["Clean the jobs", "Load the jobs into PostgreSQL"]


def test_no_geocoding_flag_is_passed_to_the_cleaning_step(monkeypatch):
    received = []
    monkeypatch.setattr(run_pipeline.clean_jobs, "main", lambda argv=None: received.append(argv) or 0)

    steps = run_pipeline.build_steps(skip_fetch=True, skip_geocoding=True)
    steps[0][1]()                                       # run the cleaning step
    assert received == [["--no-geocoding"]]


def test_main_runs_all_three_real_step_functions(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(run_pipeline, "LOG_FILE", tmp_path / "logs" / "pipeline.log")
    monkeypatch.setattr(run_pipeline.fetch_arbeitnow, "main", lambda: calls.append("fetch") or 0)
    monkeypatch.setattr(run_pipeline.clean_jobs, "main", lambda argv=None: calls.append("clean") or 0)
    monkeypatch.setattr(run_pipeline.load_jobs, "main", lambda: calls.append("load") or 0)

    assert run_pipeline.main([]) == 0
    assert calls == ["fetch", "clean", "load"]
    assert (tmp_path / "logs" / "pipeline.log").exists()   # the log file was written