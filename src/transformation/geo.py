"""
Location helpers for the transformation step.

Arbeitnow only gives a free-text "location" (for example "Berlin" or "Wien, Austria"),
so we work out the country ourselves and attach a latitude / longitude for the map.

This file is ASCII only on purpose, so it can never break because of text encoding.
"""

import re
import unicodedata

# Rough center of each country (latitude, longitude). Used for map markers.
COUNTRY_COORDS = {
    "Germany": (51.1657, 10.4515), "Austria": (47.5162, 14.5501),
    "Switzerland": (46.8182, 8.2275), "Netherlands": (52.1326, 5.2913),
    "Belgium": (50.5039, 4.4699), "France": (46.2276, 2.2137),
    "Spain": (40.4637, -3.7492), "Portugal": (39.3999, -8.2245),
    "Italy": (41.8719, 12.5674), "United Kingdom": (55.3781, -3.4360),
    "Ireland": (53.1424, -7.6921), "Luxembourg": (49.8153, 6.1296),
    "Denmark": (56.2639, 9.5018), "Sweden": (60.1282, 18.6435),
    "Norway": (60.4720, 8.4689), "Finland": (61.9241, 25.7482),
    "Iceland": (64.9631, -19.0208), "Poland": (51.9194, 19.1451),
    "Czechia": (49.8175, 15.4730), "Slovakia": (48.6690, 19.6990),
    "Hungary": (47.1625, 19.5033), "Romania": (45.9432, 24.9668),
    "Bulgaria": (42.7339, 25.4858), "Greece": (39.0742, 21.8243),
    "Croatia": (45.1000, 15.2000), "Slovenia": (46.1512, 14.9955),
    "Serbia": (44.0165, 21.0059), "Estonia": (58.5953, 25.0136),
    "Latvia": (56.8796, 24.6032), "Lithuania": (55.1694, 23.8813),
    "Cyprus": (35.1264, 33.4299), "Malta": (35.9375, 14.3754),
    "Turkey": (38.9637, 35.2433), "Ukraine": (48.3794, 31.1656),
    "United States": (37.0902, -95.7129), "Canada": (56.1304, -106.3468),
    "Mexico": (23.6345, -102.5528), "Brazil": (-14.2350, -51.9253),
    "Argentina": (-38.4161, -63.6167), "India": (20.5937, 78.9629),
    "China": (35.8617, 104.1954), "Japan": (36.2048, 138.2529),
    "Singapore": (1.3521, 103.8198), "Australia": (-25.2744, 133.7751),
    "New Zealand": (-40.9006, 174.8860), "South Africa": (-30.5595, 22.9375),
    "United Arab Emirates": (23.4241, 53.8478), "Israel": (31.0461, 34.8516),
}

# Other names people use for the same country (all lowercase, no accents).
COUNTRY_ALIASES = {
    "deutschland": "Germany", "osterreich": "Austria", "schweiz": "Switzerland",
    "suisse": "Switzerland", "svizzera": "Switzerland", "nederland": "Netherlands",
    "the netherlands": "Netherlands", "holland": "Netherlands", "belgique": "Belgium",
    "belgie": "Belgium", "uk": "United Kingdom", "great britain": "United Kingdom",
    "england": "United Kingdom", "scotland": "United Kingdom", "usa": "United States",
    "us": "United States", "united states of america": "United States",
    "czech republic": "Czechia", "espana": "Spain", "italia": "Italy",
    "polska": "Poland", "sverige": "Sweden", "norge": "Norway", "danmark": "Denmark",
    "suomi": "Finland", "uae": "United Arab Emirates", "turkiye": "Turkey",
}

# City -> country (lowercase, no accents). Add more cities here whenever the log
# shows locations that were not recognised.
_CITIES_BY_COUNTRY = {
    "Germany": [
        "berlin", "hamburg", "munich", "munchen", "cologne", "koln", "frankfurt",
        "frankfurt am main", "stuttgart", "dusseldorf", "dortmund", "essen", "leipzig",
        "bremen", "dresden", "hanover", "hannover", "nuremberg", "nurnberg", "duisburg",
        "bochum", "wuppertal", "bielefeld", "bonn", "munster", "karlsruhe", "mannheim",
        "augsburg", "wiesbaden", "mainz", "aachen", "kiel", "freiburg", "potsdam",
        "heidelberg", "darmstadt", "ulm", "regensburg", "ingolstadt", "wolfsburg",
        "braunschweig", "erfurt", "rostock", "jena", "kassel", "osnabruck", "saarbrucken",
        "magdeburg", "chemnitz", "lubeck", "luebeck", "gottingen", "paderborn", "bayreuth",
        "bamberg", "wurzburg", "konstanz", "erlangen", "oldenburg", "halle", "ludwigshafen",
        "leverkusen", "neuss", "oberhausen", "gelsenkirchen", "krefeld", "pforzheim",
        "reutlingen", "heilbronn", "furth", "trier", "koblenz", "siegen", "hagen", "hamm",
        "mulheim", "moers", "cottbus", "schwerin", "flensburg", "passau", "landshut",
        "ratingen", "bergisch gladbach", "troisdorf", "garching", "unterschleissheim",
    ],
    "Austria": ["vienna", "wien", "graz", "linz", "salzburg", "innsbruck", "klagenfurt",
                "dornbirn", "villach"],
    "Switzerland": ["zurich", "geneva", "geneve", "genf", "basel", "bern", "lausanne",
                    "lugano", "luzern", "lucerne", "zug", "winterthur", "st gallen"],
    "Netherlands": ["amsterdam", "rotterdam", "the hague", "den haag", "utrecht",
                    "eindhoven", "groningen", "delft", "veldhoven"],
    "Belgium": ["brussels", "bruxelles", "antwerp", "ghent", "leuven"],
    "France": ["paris", "lyon", "marseille", "toulouse", "nice", "nantes", "strasbourg"],
    "Spain": ["madrid", "barcelona", "valencia", "seville", "malaga"],
    "Portugal": ["lisbon", "porto"],
    "Italy": ["milan", "rome", "turin", "bologna"],
    "United Kingdom": ["london", "manchester", "edinburgh", "cambridge", "oxford", "bristol"],
    "Ireland": ["dublin", "cork", "galway"],
    "Luxembourg": ["luxembourg"],
    "Denmark": ["copenhagen", "aarhus"],
    "Sweden": ["stockholm", "gothenburg", "malmo"],
    "Norway": ["oslo", "bergen"],
    "Finland": ["helsinki", "espoo", "tampere"],
    "Poland": ["warsaw", "krakow", "wroclaw", "gdansk", "poznan"],
    "Czechia": ["prague", "brno"],
    "Hungary": ["budapest"],
    "Romania": ["bucharest", "cluj-napoca"],
    "Greece": ["athens"],
    "United States": ["new york", "san francisco", "los angeles", "seattle", "boston",
                      "austin", "chicago"],
    "Canada": ["toronto", "vancouver", "montreal"],
    "Singapore": ["singapore"],
    "India": ["bangalore", "bengaluru", "mumbai", "hyderabad", "delhi", "pune"],
}

CITY_TO_COUNTRY = {
    city: country for country, cities in _CITIES_BY_COUNTRY.items() for city in cities
}


def normalize(text):
    """Lowercase text and remove accents, so 'Z\u00fcrich' and 'zurich' match."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("\u00df", "ss").strip().lower()


# name (normalized) -> official country name
_COUNTRY_LOOKUP = {normalize(name): name for name in COUNTRY_COORDS}
_COUNTRY_LOOKUP.update(COUNTRY_ALIASES)


def country_from_name(name):
    """Return the official country name for 'Deutschland', 'germany', ... or None."""
    return _COUNTRY_LOOKUP.get(normalize(name))


# Words that mean "not a real place" (we cannot put these on a map).
NON_PLACE_WORDS = (
    "remote", "homeoffice", "home office", "hybrid", "flexible", "anywhere", "worldwide",
    "global", "online", "europe", "emea", "nationwide", "deutschlandweit", "bundesweit",
    "various", "multiple",
)


def clean_place_name(text):
    """'Paris Office' -> 'Paris', 'Berlin 10115' -> 'Berlin', 'Hamburg - Nord' -> 'Hamburg'."""
    text = re.sub(r"\(.*?\)", "", str(text))
    text = re.sub(r"\d+", " ", text)                      # postal codes
    text = re.split(r"\s+-\s+", text)[0]
    text = re.sub(r"\b(office|hq|headquarters|area|region|metropolitan)\b", " ", text,
                  flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip(" ,.-")


def is_place_name(text):
    """True when the text looks like a real place name."""
    name = normalize(text)
    return len(name) >= 2 and not any(word in name for word in NON_PLACE_WORDS)


def split_location(location):
    """Turn a free-text location into (city, country).

    Examples:
        "Berlin"            -> ("Berlin", "Germany")
        "Wien, Austria"     -> ("Wien", "Austria")
        "Hamburg (Remote)"  -> ("Hamburg", "Germany")
        "Paris Office"      -> ("Paris", "France")
        "Remote job"        -> (None, "Remote")
        "Somewhere"         -> ("Somewhere", "Unknown")   (the geocoder may find it later)
    """
    if not location or not str(location).strip():
        return None, "Unknown"

    text = re.sub(r"\(.*?\)", "", str(location))      # remove "(Remote)" notes
    text = re.split(r"[/|;]", text)[0]                # "Berlin / Hamburg" -> "Berlin"
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if not parts:
        return None, "Unknown"

    first = parts[0]
    first_is_country = country_from_name(first)

    # The country can be the last part ("Wien, Austria") or the whole text ("Germany").
    country = first_is_country
    if len(parts) > 1:
        country = country_from_name(parts[-1]) or country

    city = None if first_is_country else clean_place_name(first)
    if city and not is_place_name(city):
        city = None

    if country:
        return city, country
    if city:
        return city, CITY_TO_COUNTRY.get(normalize(city), "Unknown")
    if any(word in normalize(text) for word in NON_PLACE_WORDS):
        return None, "Remote"
    return None, "Unknown"


def coordinates_for(country):
    """Return (latitude, longitude) for a country, or (None, None) if unknown."""
    return COUNTRY_COORDS.get(country, (None, None))


# ---------------------------------------------------------------------------
# City coordinates (so the map can show jobs in the right city)
# ---------------------------------------------------------------------------
# Free geocoding service, no API key: https://open-meteo.com/en/docs/geocoding-api
# Every answer is saved in a cache file, so each city is only asked for ONCE.
import csv
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CITY_CACHE_FILE = PROJECT_ROOT / "data" / "processed" / "city_coordinates.csv"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
CACHE_COLUMNS = ["lookup", "city", "country_hint", "latitude", "longitude", "country", "found"]


def city_key(city, country):
    """The name under which a city is stored in the cache."""
    hint = normalize(country) if country and country not in ("Unknown", "Remote") else ""
    return f"{normalize(city)}|{hint}"


def load_city_cache(cache_file=None):
    """Read the cache file into a dictionary (empty if the file does not exist yet)."""
    cache_file = Path(cache_file or CITY_CACHE_FILE)
    cache = {}
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                row["found"] = row.get("found") == "1"
                cache[row["lookup"]] = row
    return cache


def save_city_cache(cache, cache_file=None):
    cache_file = Path(cache_file or CITY_CACHE_FILE)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CACHE_COLUMNS)
        writer.writeheader()
        for row in cache.values():
            writer.writerow({**row, "found": "1" if row.get("found") else "0"})


def _search_places(session, name, count):
    """Call the geocoding service. Raises RuntimeError when the service is not reachable."""
    import requests

    try:
        response = session.get(
            GEOCODING_URL,
            params={"name": name, "count": count, "language": "en", "format": "json"},
            timeout=(5, 15),
        )
        response.raise_for_status()
        return response.json().get("results") or []
    except (requests.RequestException, ValueError) as error:
        raise RuntimeError(str(error))


def lookup_city_online(session, city, country_hint):
    """Find a city. Returns {'latitude', 'longitude', 'country'} or None if not found."""
    known = bool(country_hint) and country_hint not in ("Unknown", "Remote")

    def same_country(result):
        name = result.get("country") or ""
        return country_from_name(name) == country_hint or normalize(name) == normalize(country_hint)

    if known:
        results = _search_places(session, f"{city}, {country_hint}", 5)
        match = next((item for item in results if same_country(item)), None)
        if match is None:  # try again with only the city name, then check the country ourselves
            results = _search_places(session, city, 10)
            match = next((item for item in results if same_country(item)), None)
    else:
        results = _search_places(session, city, 5)
        match = results[0] if results else None

    if match is None:
        return None
    return {
        "latitude": match["latitude"],
        "longitude": match["longitude"],
        "country": match.get("country") or "",
    }


def add_city_coordinates(dataframe, lookup=None, pause=0.15, cache_file=None):
    """Give every job the coordinates of its CITY (and a country when it was Unknown).

    lookup(city, country_hint) can be replaced in tests; by default the free online
    service is used. Cities that cannot be found keep their country coordinates.
    """
    cache = load_city_cache(cache_file)

    pairs = {}
    for city, country in zip(dataframe["city"], dataframe["country"]):
        if isinstance(city, str) and is_place_name(city):
            pairs[city_key(city, country)] = (city, country)
    missing = [(key, pair) for key, pair in pairs.items() if key not in cache]

    if missing:
        session = None
        if lookup is None:
            import requests

            session = requests.Session()
            session.headers.update({"User-Agent": "global-job-market-pipeline/0.1 (learning project)"})
            lookup = lambda city, hint: lookup_city_online(session, city, hint)  # noqa: E731

        logger.info("Looking up %s new cities (cities already known: %s).",
                    len(missing), len(pairs) - len(missing))
        errors = 0
        try:
            for number, (key, (city, country)) in enumerate(missing, start=1):
                try:
                    result = lookup(city, country)
                except RuntimeError as error:
                    errors += 1
                    logger.warning("Lookup failed for %r: %s", city, error)
                    if errors >= 5:
                        logger.warning("Too many errors in a row. Stopping the city lookup; "
                                       "run the script again later to continue.")
                        break
                    continue
                errors = 0
                cache[key] = {
                    "lookup": key, "city": city, "country_hint": country,
                    "latitude": result["latitude"] if result else "",
                    "longitude": result["longitude"] if result else "",
                    "country": result["country"] if result else "",
                    "found": bool(result),
                }
                if number % 25 == 0:
                    logger.info("  looked up %s of %s cities ...", number, len(missing))
                time.sleep(pause)
        finally:
            save_city_cache(cache, cache_file)   # keep the progress, even if stopped early

    latitudes, longitudes, countries, precisions = [], [], [], []
    for city, country, lat, lng in zip(dataframe["city"], dataframe["country"],
                                       dataframe["latitude"], dataframe["longitude"]):
        entry = cache.get(city_key(city, country)) if isinstance(city, str) else None
        if entry and entry["found"]:
            latitudes.append(float(entry["latitude"]))
            longitudes.append(float(entry["longitude"]))
            if country == "Unknown" and entry["country"]:
                country = country_from_name(entry["country"]) or entry["country"]
            precisions.append("city")
        else:
            latitudes.append(lat)
            longitudes.append(lng)
            precisions.append("country" if lat == lat and lat is not None else "none")  # lat == lat: not NaN
        countries.append(country)

    dataframe = dataframe.copy()
    dataframe["latitude"], dataframe["longitude"] = latitudes, longitudes
    dataframe["country"], dataframe["location_precision"] = countries, precisions
    return dataframe