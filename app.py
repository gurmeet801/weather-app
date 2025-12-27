import os

from flask import Flask, make_response, render_template, request

from services.geocode_service import geocode_address
from services.weather_service import fetch_forecast

app = Flask(__name__)


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

    if lat and lon:
        forecast, error = fetch_forecast(lat, lon)
        search_source = "Current location"
    elif address:
        lat, lon, resolved_location, error = geocode_address(address)
        search_source = "Address search"
        if not error:
            forecast, error = fetch_forecast(lat, lon)
    elif cached_lat and cached_lon:
        lat, lon = cached_lat, cached_lon
        forecast, error = fetch_forecast(lat, lon)
        search_source = "Recent location"
        used_cached_location = True

    response = make_response(
        render_template(
            "index.html",
            address=address,
            forecast=forecast,
            error=error,
            resolved_location=resolved_location,
            search_source=search_source,
            used_cached_location=used_cached_location,
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(debug=True, host="0.0.0.0", port=port)
