import os

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

DEFAULT_LAT = "37.7749"
DEFAULT_LON = "-122.4194"
WEATHER_GOV_USER_AGENT = os.getenv(
    "WEATHER_GOV_USER_AGENT", "(weather.jawand.dev, jawandsingh@gmail.com)"
)
WEATHER_GOV_HEADERS = {
    "User-Agent": WEATHER_GOV_USER_AGENT,
    "Accept": "application/geo+json",
}
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_HEADERS = {
    "User-Agent": WEATHER_GOV_USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en",
}


def fetch_forecast(lat_value, lon_value):
    if isinstance(lat_value, str):
        lat_value = lat_value.strip()
    if isinstance(lon_value, str):
        lon_value = lon_value.strip()
    try:
        lat = float(lat_value)
        lon = float(lon_value)
    except (TypeError, ValueError):
        return None, "Enter valid decimal coordinates."

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, "Coordinates are out of range."

    points_url = f"https://api.weather.gov/points/{lat},{lon}"

    try:
        points_response = requests.get(
            points_url, headers=WEATHER_GOV_HEADERS, timeout=10
        )
        points_response.raise_for_status()
    except requests.HTTPError:
        return None, "Weather.gov returned an error for those coordinates."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    points_data = points_response.json()
    points_props = points_data.get("properties", {})
    forecast_url = points_props.get("forecast")
    if not forecast_url:
        return None, "No forecast URL available for that location."

    try:
        forecast_response = requests.get(
            forecast_url, headers=WEATHER_GOV_HEADERS, timeout=10
        )
        forecast_response.raise_for_status()
    except requests.HTTPError:
        return None, "Weather.gov returned an error for the forecast request."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    forecast_data = forecast_response.json()
    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        return None, "No forecast periods available for that location."

    location_props = (
        points_props.get("relativeLocation", {}).get("properties", {}) or {}
    )
    city = location_props.get("city")
    state = location_props.get("state")
    location = f"{city}, {state}" if city and state else "Forecast location"

    return {
        "location": location,
        "period": periods[0],
        "next_period": periods[1] if len(periods) > 1 else None,
    }, None


def geocode_address(address):
    if address is None:
        return None, None, None, "Enter an address."

    query = address.strip()
    if not query:
        return None, None, None, "Enter an address."

    try:
        response = requests.get(
            GEOCODER_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers=GEOCODER_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
    except requests.HTTPError:
        return None, None, None, "Geocoding service returned an error."
    except requests.RequestException:
        return None, None, None, "Could not reach the geocoding service."

    results = response.json()
    if not results:
        return None, None, None, "No results found for that address."

    result = results[0]
    lat = result.get("lat")
    lon = result.get("lon")
    display_name = result.get("display_name")
    if not lat or not lon:
        return None, None, None, "No coordinates returned for that address."

    return lat, lon, display_name, None


@app.route("/")
def index():
    address = request.args.get("address", "").strip()
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    forecast = None
    error = None
    resolved_location = None
    search_source = "Default location"

    if lat and lon:
        forecast, error = fetch_forecast(lat, lon)
        search_source = "Current location"
    elif address:
        lat, lon, resolved_location, error = geocode_address(address)
        search_source = "Address search"
        if not error:
            forecast, error = fetch_forecast(lat, lon)
    else:
        forecast, error = fetch_forecast(DEFAULT_LAT, DEFAULT_LON)

    return render_template(
        "index.html",
        address=address,
        forecast=forecast,
        error=error,
        resolved_location=resolved_location,
        search_source=search_source,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(debug=True, host="0.0.0.0", port=port)
