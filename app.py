import os

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

DEFAULT_LAT = "37.7749"
DEFAULT_LON = "-122.4194"
WEATHER_GOV_HEADERS = {
    "User-Agent": "(weather.jawand.dev, jawandsingh@gmail.com)",
    "Accept": "application/geo+json",
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


@app.route("/")
def index():
    lat = request.args.get("lat", DEFAULT_LAT)
    lon = request.args.get("lon", DEFAULT_LON)
    forecast, error = fetch_forecast(lat, lon)
    return render_template(
        "index.html",
        lat=lat,
        lon=lon,
        forecast=forecast,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)
