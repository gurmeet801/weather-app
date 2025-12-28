import re
import time
from threading import Lock

import requests

from utils import cached_get_json, get_geocoder_headers

GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_HEADERS = get_geocoder_headers()
ZIP_RE = re.compile(r"^\d{5}(?:-\d{4})?$")
ZIP9_RE = re.compile(r"^\d{9}$")
NOMINATIM_MIN_INTERVAL = 1.0
_NOMINATIM_LOCK = Lock()
_last_nominatim_request = 0.0


def _throttle_nominatim():
    global _last_nominatim_request
    with _NOMINATIM_LOCK:
        now = time.monotonic()
        wait = NOMINATIM_MIN_INTERVAL - (now - _last_nominatim_request)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim_request = time.monotonic()


def _normalize_zip(query):
    if ZIP_RE.match(query):
        return query
    if ZIP9_RE.match(query):
        return f"{query[:5]}-{query[5:]}"
    return None


def _normalize_state(address_info):
    if not isinstance(address_info, dict):
        return None
    state_code = address_info.get("state_code")
    if state_code:
        normalized = str(state_code).strip().upper()
        return normalized or None
    iso_code = address_info.get("ISO3166-2-lvl4") or address_info.get("ISO3166-2-lvl5")
    if iso_code:
        iso_code = str(iso_code).strip()
        if iso_code.upper().startswith("US-"):
            candidate = iso_code.split("-")[-1].strip().upper()
            if len(candidate) == 2:
                return candidate
    state = address_info.get("state")
    if isinstance(state, str):
        return state.strip()
    return state


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
                    "addressdetails": 1,
                },
                headers=GEOCODER_HEADERS,
                ttl=24 * 60 * 60,
                cache_group="geocode",
                throttle=_throttle_nominatim,
            )
            if not results:
                results = cached_get_json(
                    GEOCODER_URL,
                    params={
                        "q": f"{zip_code} USA",
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1,
                    },
                    headers=GEOCODER_HEADERS,
                    ttl=24 * 60 * 60,
                    cache_group="geocode",
                    throttle=_throttle_nominatim,
                )
        else:
            results = cached_get_json(
                GEOCODER_URL,
                params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
                headers=GEOCODER_HEADERS,
                ttl=24 * 60 * 60,
                cache_group="geocode",
                throttle=_throttle_nominatim,
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
    state = _normalize_state(address_info)

    return lat, lon, city, state, display_name, None


def geocode_place(query):
    if query is None:
        return None, None
    cleaned = query.strip()
    if not cleaned:
        return None, None
    try:
        results = cached_get_json(
            GEOCODER_URL,
            params={
                "q": cleaned,
                "format": "json",
                "limit": 1,
                "countrycodes": "us",
            },
            headers=GEOCODER_HEADERS,
            ttl=7 * 24 * 60 * 60,
            cache_group="geocode_places",
            throttle=_throttle_nominatim,
        )
    except requests.HTTPError:
        return None, None
    except requests.RequestException:
        return None, None

    if not results:
        return None, None

    result = results[0]
    lat = result.get("lat")
    lon = result.get("lon")
    if not lat or not lon:
        return None, None
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None
