import requests

from utils import (
    cached_get_json,
    format_alert_time,
    format_hour_label,
    get_weather_headers,
    parse_iso_datetime,
)

WEATHER_GOV_HEADERS = get_weather_headers()


def build_hourly_today(periods):
    if not periods:
        return []
    hourly = []
    first_day = None
    for period in periods:
        dt = parse_iso_datetime(period.get("startTime"))
        if not dt:
            continue
        if first_day is None:
            first_day = dt.date()
        if dt.date() != first_day:
            continue
        hourly.append(
            {
                "time": format_hour_label(dt),
                "temperature": period.get("temperature"),
                "temperatureUnit": period.get("temperatureUnit"),
                "shortForecast": period.get("shortForecast"),
            }
        )
    return hourly


def build_daily_forecast(periods, limit=7):
    daily = []
    for period in periods or []:
        if not period.get("isDaytime"):
            continue
        daily.append(
            {
                "name": period.get("name"),
                "temperature": period.get("temperature"),
                "temperatureUnit": period.get("temperatureUnit"),
                "shortForecast": period.get("shortForecast"),
            }
        )
        if len(daily) >= limit:
            break
    return daily


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
        points_data = cached_get_json(
            points_url, headers=WEATHER_GOV_HEADERS, ttl=12 * 60 * 60
        )
    except requests.HTTPError:
        return None, "Weather.gov returned an error for those coordinates."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    points_props = points_data.get("properties", {})
    forecast_url = points_props.get("forecast")
    hourly_url = points_props.get("forecastHourly")
    if not forecast_url:
        return None, "No forecast URL available for that location."

    try:
        forecast_data = cached_get_json(
            forecast_url, headers=WEATHER_GOV_HEADERS, ttl=10 * 60
        )
    except requests.HTTPError:
        return None, "Weather.gov returned an error for the forecast request."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        return None, "No forecast periods available for that location."

    location_props = (
        points_props.get("relativeLocation", {}).get("properties", {}) or {}
    )
    city = location_props.get("city")
    state = location_props.get("state")
    location = f"{city}, {state}" if city and state else "Forecast location"

    hourly_today = []
    hourly_error = None
    if hourly_url:
        try:
            hourly_data = cached_get_json(
                hourly_url, headers=WEATHER_GOV_HEADERS, ttl=10 * 60
            )
            hourly_periods = hourly_data.get("properties", {}).get("periods", [])
            hourly_today = build_hourly_today(hourly_periods)
        except requests.HTTPError:
            hourly_error = "Hourly forecast unavailable."
        except requests.RequestException:
            hourly_error = "Could not reach api.weather.gov."
    else:
        hourly_error = "Hourly forecast unavailable."

    alerts = []
    alerts_error = None
    alerts_url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
    try:
        alerts_data = cached_get_json(
            alerts_url, headers=WEATHER_GOV_HEADERS, ttl=5 * 60
        )
        for feature in alerts_data.get("features", []) or []:
            props = feature.get("properties", {}) or {}
            alerts.append(
                {
                    "title": props.get("headline") or props.get("event"),
                    "severity": props.get("severity"),
                    "area": props.get("areaDesc"),
                    "ends": format_alert_time(props.get("ends")),
                }
            )
    except requests.HTTPError:
        alerts_error = "Alerts unavailable."
    except requests.RequestException:
        alerts_error = "Could not reach api.weather.gov."

    return {
        "location": location,
        "period": periods[0],
        "next_period": periods[1] if len(periods) > 1 else None,
        "hourly_today": hourly_today,
        "hourly_error": hourly_error,
        "daily_forecast": build_daily_forecast(periods),
        "alerts": alerts,
        "alerts_error": alerts_error,
    }, None
