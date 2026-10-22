"""
Tests for src/transformation/geo.py (location cleaning and city coordinates).

These tests need NO internet and NO database: the online city service is replaced
by a small fake function, so they run in a second.

Run them from the project's main folder:   pytest
"""

import pandas as pd
import pytest

from src.transformation import geo


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text, expected",
    [
        ("Z\u00fcrich", "zurich"),
        ("  Berlin ", "berlin"),
        ("K\u00f6ln", "koln"),
        ("Stra\u00dfe", "strasse"),
        ("M\u00dcNCHEN", "munchen"),
    ],
)
def test_normalize_removes_accents_and_lowercases(text, expected):
    assert geo.normalize(text) == expected


# ---------------------------------------------------------------------------
# country names
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "name, expected",
    [
        ("Germany", "Germany"),
        ("deutschland", "Germany"),
        ("Schweiz", "Switzerland"),
        ("The Netherlands", "Netherlands"),
        ("UK", "United Kingdom"),
        ("Czech Republic", "Czechia"),
        ("Atlantis", None),
        ("", None),
    ],
)
def test_country_from_name(name, expected):
    assert geo.country_from_name(name) == expected


def test_coordinates_for_known_and_unknown_country():
    latitude, longitude = geo.coordinates_for("Germany")
    assert 47 < latitude < 55 and 5 < longitude < 16
    assert geo.coordinates_for("Unknown") == (None, None)
    assert geo.coordinates_for("Remote") == (None, None)


# ---------------------------------------------------------------------------
# split_location: free text -> (city, country)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "location, expected",
    [
        ("Berlin", ("Berlin", "Germany")),
        ("Wien, Austria", ("Wien", "Austria")),
        ("Hamburg (Remote)", ("Hamburg", "Germany")),
        ("Paris Office", ("Paris", "France")),
        ("Berlin 10115", ("Berlin", "Germany")),
        ("Berlin / Hamburg", ("Berlin", "Germany")),
        ("Deutschland", (None, "Germany")),
        ("Remote, Germany", (None, "Germany")),
        ("Remote job", (None, "Remote")),
        ("Homeoffice", (None, "Remote")),
        ("Atlantis", ("Atlantis", "Unknown")),
        ("", (None, "Unknown")),
        (None, (None, "Unknown")),
    ],
)
def test_split_location(location, expected):
    assert geo.split_location(location) == expected


def test_clean_place_name_and_is_place_name():
    assert geo.clean_place_name("Hamburg - Nord") == "Hamburg"
    assert geo.clean_place_name("Zurich HQ") == "Zurich"
    assert geo.is_place_name("Berlin") is True
    assert geo.is_place_name("Remote job") is False
    assert geo.is_place_name("x") is False


# ---------------------------------------------------------------------------
# the city cache file
# ---------------------------------------------------------------------------
def test_city_cache_roundtrip(tmp_path):
    cache_file = tmp_path / "cities.csv"
    cache = {
        "berlin|germany": {
            "lookup": "berlin|germany", "city": "Berlin", "country_hint": "Germany",
            "latitude": 52.52, "longitude": 13.4, "country": "Germany", "found": True,
        },
        "nowhere|": {
            "lookup": "nowhere|", "city": "Nowhere", "country_hint": "Unknown",
            "latitude": "", "longitude": "", "country": "", "found": False,
        },
    }
    geo.save_city_cache(cache, cache_file)
    loaded = geo.load_city_cache(cache_file)

    assert loaded["berlin|germany"]["found"] is True
    assert float(loaded["berlin|germany"]["latitude"]) == 52.52
    assert loaded["nowhere|"]["found"] is False


def test_load_city_cache_of_missing_file_is_empty(tmp_path):
    assert geo.load_city_cache(tmp_path / "does_not_exist.csv") == {}


# ---------------------------------------------------------------------------
# add_city_coordinates (with a fake city service)
# ---------------------------------------------------------------------------
def make_jobs():
    return pd.DataFrame(
        {
            "city": ["Berlin", "Berlin", "Baar", "Nowhereville", None, "Remote job"],
            "country": ["Germany", "Germany", "Unknown", "Unknown", "Remote", "Remote"],
            "latitude": [51.0, 51.0, None, None, None, None],
            "longitude": [10.0, 10.0, None, None, None, None],
        }
    )


FAKE_PLACES = {
    "Berlin": {"latitude": 52.52, "longitude": 13.4, "country": "Germany"},
    "Baar": {"latitude": 47.19, "longitude": 8.53, "country": "Switzerland"},
}


def test_add_city_coordinates_fills_city_position_and_country(tmp_path):
    asked = []

    def fake_lookup(city, country_hint):
        asked.append(city)
        return FAKE_PLACES.get(city)

    result = geo.add_city_coordinates(
        make_jobs(), lookup=fake_lookup, pause=0, cache_file=tmp_path / "cache.csv"
    )

    # Berlin appears twice but is only looked up once.
    assert sorted(asked) == ["Baar", "Berlin", "Nowhereville"]

    berlin = result.iloc[0]
    assert berlin["location_precision"] == "city"
    assert berlin["latitude"] == 52.52 and berlin["longitude"] == 13.4

    # An Unknown country is discovered from the city.
    baar = result.iloc[2]
    assert baar["country"] == "Switzerland"
    assert baar["location_precision"] == "city"

    # A city that cannot be found stays without position.
    assert result.iloc[3]["country"] == "Unknown"
    assert result.iloc[3]["location_precision"] == "none"

    # Remote jobs without a real place are never looked up.
    assert result.iloc[4]["location_precision"] == "none"
    assert result.iloc[5]["location_precision"] == "none"


def test_add_city_coordinates_keeps_country_position_when_city_not_found(tmp_path):
    jobs = pd.DataFrame(
        {"city": ["Smallville"], "country": ["Germany"], "latitude": [51.0], "longitude": [10.0]}
    )
    result = geo.add_city_coordinates(
        jobs, lookup=lambda city, hint: None, pause=0, cache_file=tmp_path / "cache.csv"
    )
    assert result.iloc[0]["location_precision"] == "country"
    assert result.iloc[0]["latitude"] == 51.0


def test_second_run_uses_the_cache_and_asks_nothing(tmp_path):
    cache_file = tmp_path / "cache.csv"
    geo.add_city_coordinates(
        make_jobs(), lookup=lambda c, h: FAKE_PLACES.get(c), pause=0, cache_file=cache_file
    )

    asked = []

    def second_lookup(city, country_hint):
        asked.append(city)
        return FAKE_PLACES.get(city)

    geo.add_city_coordinates(make_jobs(), lookup=second_lookup, pause=0, cache_file=cache_file)
    assert asked == []


def test_lookup_errors_stop_after_five_and_progress_is_saved(tmp_path):
    cities = [f"City{number}" for number in range(10)]
    jobs = pd.DataFrame(
        {"city": cities, "country": ["Germany"] * 10,
         "latitude": [51.0] * 10, "longitude": [10.0] * 10}
    )
    attempts = []

    def broken_lookup(city, country_hint):
        attempts.append(city)
        raise RuntimeError("service is down")

    cache_file = tmp_path / "cache.csv"
    result = geo.add_city_coordinates(jobs, lookup=broken_lookup, pause=0, cache_file=cache_file)

    assert len(attempts) == 5                      # stopped after 5 errors in a row
    assert (result["location_precision"] == "country").all()
    assert cache_file.exists()                     # the cache file was still written


# ---------------------------------------------------------------------------
# lookup_city_online (with a fake web session)
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, results):
        self.results = results

    def raise_for_status(self):
        pass

    def json(self):
        return {"results": self.results} if self.results else {}


class FakeSession:
    def __init__(self, answers):
        self.answers = answers
        self.asked = []

    def get(self, url, params=None, timeout=None):
        self.asked.append(params["name"])
        return FakeResponse(self.answers.get(params["name"]))


def test_lookup_city_online_picks_the_result_in_the_right_country():
    session = FakeSession({
        "Paris, France": None,
        "Paris": [
            {"latitude": 33.6, "longitude": -95.5, "country": "United States"},
            {"latitude": 48.85, "longitude": 2.35, "country": "France"},
        ],
    })
    result = geo.lookup_city_online(session, "Paris", "France")

    assert result["country"] == "France"
    assert session.asked == ["Paris, France", "Paris"]   # second try with the plain name


def test_lookup_city_online_rejects_a_wrong_country():
    wrong = [{"latitude": 44.4, "longitude": -71.1, "country": "United States"}]
    session = FakeSession({"Berlin, Austria": wrong, "Berlin": wrong})
    assert geo.lookup_city_online(session, "Berlin", "Austria") is None


def test_lookup_city_online_unknown_country_takes_first_result():
    session = FakeSession({"Baar": [{"latitude": 47.19, "longitude": 8.53, "country": "Switzerland"}]})
    result = geo.lookup_city_online(session, "Baar", "Unknown")
    assert result["country"] == "Switzerland"