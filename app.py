import os

from flask import Flask, make_response, render_template, request

from services.geocode_service import geocode_address
from services.weather_service import fetch_forecast
from utils import (
    clear_cache,
    clear_location_cache,
    delete_location_cache,
    format_location_key,
    format_coordinate_alias,
    list_cached_locations,
    register_location_alias,
)

app = Flask(__name__)


@app.route("/manifest.webmanifest")
def manifest():
    response = make_response(app.send_static_file("manifest.webmanifest"))
    response.headers["Content-Type"] = "application/manifest+json"
    return response


@app.route("/sw.js")
def service_worker():
    response = make_response(app.send_static_file("sw.js"))
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/")
def index():
    address = request.args.get("address", "").strip()
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    cached_lat = request.cookies.get("last_lat")
    cached_lon = request.cookies.get("last_lon")
    forecast = None
    error = None
    resolved_location = None
    search_source = None
    used_cached_location = False
    current_location_key = None

    if lat and lon:
        forecast, error = fetch_forecast(lat, lon)
        search_source = "Current location"
        if forecast and not error:
            current_location_key = forecast.get("location_key")
    elif address:
        lat, lon, city, state, resolved_location, error = geocode_address(address)
        search_source = "Address search"
        if not error:
            forecast, error = fetch_forecast(lat, lon)
            if forecast and not error:
                current_location_key = forecast.get("location_key")
                # Register alias from address to canonical location
                if city and state:
                    address_alias = f"addr:{address.lower()}"
                    canonical_key = format_location_key(city, state)
                    register_location_alias(address_alias, canonical_key)
    elif cached_lat and cached_lon:
        lat, lon = cached_lat, cached_lon
        forecast, error = fetch_forecast(lat, lon)
        search_source = "Recent location"
        used_cached_location = True
        if forecast and not error:
            current_location_key = forecast.get("location_key")

    cached_locations = list_cached_locations()
    response = make_response(
        render_template(
            "index.html",
            address=address,
            forecast=forecast,
            error=error,
            resolved_location=resolved_location,
            search_source=search_source,
            used_cached_location=used_cached_location,
            cached_locations=cached_locations,
            current_location_key=current_location_key,
        )
    )
    if forecast and not error and lat and lon:
        response.set_cookie(
            "last_lat",
            str(lat),
            max_age=30 * 24 * 60 * 60,
            samesite="Lax",
        )
        response.set_cookie(
            "last_lon",
            str(lon),
            max_age=30 * 24 * 60 * 60,
            samesite="Lax",
        )

    return response


@app.route("/refresh", methods=["POST"])
def refresh_cache():
    payload = request.get_json(silent=True) or {}
    location_key = payload.get("location_key") or request.form.get("location_key")
    action = payload.get("action") or request.form.get("action")
    if location_key:
        if action == "delete":
            delete_location_cache(location_key)
        else:
            clear_location_cache(location_key)
    else:
        clear_cache()
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "4200"))
    app.run(debug=False, host="0.0.0.0", port=port)
