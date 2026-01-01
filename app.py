import os
from pathlib import Path

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

STATIC_VERSION_FILES = (
    Path(__file__).resolve().parent / "static" / "styles.css",
    Path(__file__).resolve().parent / "static" / "js" / "weather.js",
    Path(__file__).resolve().parent / "static" / "sw.js",
    Path(__file__).resolve().parent / "static" / "manifest.webmanifest",
)


def _asset_version():
    mtimes = []
    for path in STATIC_VERSION_FILES:
        try:
            mtimes.append(path.stat().st_mtime)
        except OSError:
            continue
    if not mtimes:
        return "1"
    return str(int(max(mtimes)))


ASSET_VERSION = _asset_version()


@app.context_processor
def inject_asset_version():
    return {"asset_version": ASSET_VERSION}


def _get_default_location_query():
    value = os.getenv("DEFAULT_LOCATION", "16066")
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_default_location():
    query = _get_default_location_query()
    if not query:
        return None, "Default location not configured."
    lat, lon, city, state, resolved_location, error = geocode_address(query)
    if error:
        return None, error
    return {
        "query": query,
        "lat": lat,
        "lon": lon,
        "city": city,
        "state": state,
        "resolved_location": resolved_location,
    }, None


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
    defer_extras = request.args.get("eager") != "1"
    cached_lat = request.cookies.get("last_lat")
    cached_lon = request.cookies.get("last_lon")
    forecast = None
    error = None
    resolved_location = None
    search_source = None
    used_cached_location = False
    current_location_key = None

    if lat and lon:
        forecast, error = fetch_forecast(
            lat,
            lon,
            include_hourly=not defer_extras,
            include_alerts=not defer_extras,
        )
        search_source = "Current location"
        if forecast and not error:
            current_location_key = forecast.get("location_key")
    elif address:
        lat, lon, city, state, resolved_location, error = geocode_address(address)
        search_source = "Address search"
        if not error:
            forecast, error = fetch_forecast(
                lat,
                lon,
                preferred_city=city,
                preferred_state=state,
                include_hourly=not defer_extras,
                include_alerts=not defer_extras,
            )
            if forecast and not error:
                current_location_key = forecast.get("location_key")
                # Register alias from address to canonical location
                if city and state:
                    address_alias = f"addr:{address.lower()}"
                    canonical_key = format_location_key(city, state)
                    register_location_alias(address_alias, canonical_key)
    elif cached_lat and cached_lon:
        lat, lon = cached_lat, cached_lon
        forecast, error = fetch_forecast(
            lat,
            lon,
            include_hourly=not defer_extras,
            include_alerts=not defer_extras,
        )
        search_source = "Recent location"
        used_cached_location = True
        if forecast and not error:
            current_location_key = forecast.get("location_key")
    else:
        default_location, default_error = _resolve_default_location()
        if default_location:
            lat = default_location["lat"]
            lon = default_location["lon"]
            resolved_location = default_location["resolved_location"]
            search_source = "Default location"
            forecast, error = fetch_forecast(
                lat,
                lon,
                preferred_city=default_location["city"],
                preferred_state=default_location["state"],
                include_hourly=not defer_extras,
                include_alerts=not defer_extras,
            )
            if forecast and not error:
                current_location_key = forecast.get("location_key")
        else:
            error = default_error

    resolved_coords = None
    if lat is not None and lon is not None:
        lat_value = _parse_float(lat)
        lon_value = _parse_float(lon)
        if lat_value is not None and lon_value is not None:
            resolved_coords = {"lat": lat_value, "lon": lon_value}

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
            defer_extras=defer_extras,
            resolved_coords=resolved_coords,
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


@app.route("/api/extras")
def forecast_extras():
    lat_value = _parse_float(request.args.get("lat"))
    lon_value = _parse_float(request.args.get("lon"))
    if lat_value is None or lon_value is None:
        return {"error": "Missing coordinates."}, 400

    location_key = request.args.get("location_key")
    if isinstance(location_key, str):
        location_key = location_key.strip() or None

    forecast, error = fetch_forecast(
        lat_value,
        lon_value,
        preferred_location_key=location_key,
        include_hourly=True,
        include_alerts=True,
    )
    if error:
        return {"error": error}, 400

    alerts = forecast.get("alerts") or []
    has_advisory = any(
        "advisory" in (alert.get("event") or "").lower() for alert in alerts
    )
    alerts_html = render_template("components/alerts.html", forecast=forecast)

    return {
        "hourly_today": forecast.get("hourly_today", []),
        "hourly_error": forecast.get("hourly_error"),
        "daily_details": forecast.get("daily_details", []),
        "humidity": forecast.get("humidity"),
        "precip_chance": forecast.get("precip_chance"),
        "feels_like_temperature": forecast.get("feels_like_temperature"),
        "feels_like_unit": forecast.get("feels_like_unit"),
        "actual_temperature": forecast.get("actual_temperature"),
        "actual_temperature_unit": forecast.get("actual_temperature_unit"),
        "alerts_html": alerts_html,
        "alerts_has_advisory": has_advisory,
        "location_key": forecast.get("location_key"),
        "time_zone": forecast.get("time_zone"),
    }


@app.route("/warm")
def warm_default_location():
    default_location, error = _resolve_default_location()
    if error:
        return {"status": "error", "error": error}, 500

    forecast, error = fetch_forecast(
        default_location["lat"],
        default_location["lon"],
        preferred_city=default_location["city"],
        preferred_state=default_location["state"],
        include_hourly=True,
        include_alerts=True,
    )
    if error:
        return {"status": "error", "error": error}, 502

    return {
        "status": "ok",
        "location": forecast.get("location"),
        "location_key": forecast.get("location_key"),
    }


if __name__ == "__main__":
    port = int(os.getenv("WEATHER_APP_PORT", "4200"))
    app.run(debug=False, host="0.0.0.0", port=port)
