import re

import requests

from utils import cached_get_json, get_geocoder_headers

GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_HEADERS = get_geocoder_headers()
ZIP_RE = re.compile(r"^\d{5}(?:-\d{4})?$")
ZIP9_RE = re.compile(r"^\d{9}$")


def _normalize_zip(query):
    if ZIP_RE.match(query):
        return query
    if ZIP9_RE.match(query):
        return f"{query[:5]}-{query[5:]}"
    return None


def geocode_address(address):
    if address is None:
        return None, None, None, None, None, "Enter an address or ZIP code."

    query = address.strip()
    if not query:
        return None, None, None, None, None, "Enter an address or ZIP code."

    zip_code = _normalize_zip(query)

    try:
        if zip_code:
            results = cached_get_json(
                GEOCODER_URL,
                params={
                    "postalcode": zip_code,
                    "countrycodes": "us",
                    "format": "json",
                    "limit": 1,
                },
                headers=GEOCODER_HEADERS,
                ttl=24 * 60 * 60,
                cache_group="geocode",
            )
            if not results:
                results = cached_get_json(
                    GEOCODER_URL,
                    params={"q": f"{zip_code} USA", "format": "json", "limit": 1},
                    headers=GEOCODER_HEADERS,
                    ttl=24 * 60 * 60,
                    cache_group="geocode",
                )
        else:
            results = cached_get_json(
                GEOCODER_URL,
                params={"q": query, "format": "json", "limit": 1},
                headers=GEOCODER_HEADERS,
                ttl=24 * 60 * 60,
                cache_group="geocode",
            )
    except requests.HTTPError:
        return None, None, None, None, None, "Geocoding service returned an error."
    except requests.RequestException:
        return None, None, None, None, None, "Could not reach the geocoding service."

    if not results:
        return None, None, None, None, None, "No results found for that address or ZIP code."

    result = results[0]
    lat = result.get("lat")
    lon = result.get("lon")
    display_name = result.get("display_name")
    if not lat or not lon:
        return None, None, None, None, None, "No coordinates returned for that address or ZIP code."

    # Extract city and state from address details
    address_info = result.get("address", {})
    city = address_info.get("city") or address_info.get("town") or address_info.get("village") or address_info.get("hamlet")
    state = address_info.get("state")

    return lat, lon, city, state, display_name, None
