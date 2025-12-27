import requests

from utils import cached_get_json, get_geocoder_headers

GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_HEADERS = get_geocoder_headers()


def geocode_address(address):
    if address is None:
        return None, None, None, "Enter an address."

    query = address.strip()
    if not query:
        return None, None, None, "Enter an address."

    try:
        results = cached_get_json(
            GEOCODER_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers=GEOCODER_HEADERS,
            ttl=24 * 60 * 60,
        )
    except requests.HTTPError:
        return None, None, None, "Geocoding service returned an error."
    except requests.RequestException:
        return None, None, None, "Could not reach the geocoding service."

    if not results:
        return None, None, None, "No results found for that address."

    result = results[0]
    lat = result.get("lat")
    lon = result.get("lon")
    display_name = result.get("display_name")
    if not lat or not lon:
        return None, None, None, "No coordinates returned for that address."

    return lat, lon, display_name, None
