import re

import requests

from utils import (
    cached_get_json,
    format_location_key,
    format_alert_time,
    format_hour_label,
    get_weather_headers,
    location_group_key,
    parse_iso_datetime,
    register_location,
)

WEATHER_GOV_HEADERS = get_weather_headers()


def _parse_wind_speed_mph(value):
    if not value:
        return None
    numbers = re.findall(r"[-+]?\d*\.?\d+", value)
    if not numbers:
        return None
    speeds = [float(num) for num in numbers]
    return sum(speeds) / len(speeds)


def _to_fahrenheit(temp, unit):
    if unit == "C":
        return (temp * 9 / 5) + 32
    return temp


def _from_fahrenheit(temp, unit):
    if unit == "C":
        return (temp - 32) * 5 / 9
    return temp


def _calculate_feels_like(temp, unit, humidity=None, wind_mph=None):
    if temp is None:
        return None
    temp_f = _to_fahrenheit(temp, unit)
    feels_f = temp_f

    if humidity is not None and temp_f >= 80 and humidity >= 40:
        t = temp_f
        r = humidity
        feels_f = (
            -42.379
            + 2.04901523 * t
            + 10.14333127 * r
            - 0.22475541 * t * r
            - 0.00683783 * t * t
            - 0.05481717 * r * r
            + 0.00122874 * t * t * r
            + 0.00085282 * t * r * r
            - 0.00000199 * t * t * r * r
        )
    elif wind_mph is not None and temp_f <= 50 and wind_mph >= 3:
        v = wind_mph
        t = temp_f
        feels_f = 35.74 + 0.6215 * t - 35.75 * (v**0.16) + 0.4275 * t * (v**0.16)

    feels_value = _from_fahrenheit(feels_f, unit)
    return int(round(feels_value))


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

    location_key = format_location_key(lat, lon)
    cache_group = location_group_key(location_key)
    points_url = f"https://api.weather.gov/points/{lat},{lon}"

    try:
        points_data = cached_get_json(
            points_url,
            headers=WEATHER_GOV_HEADERS,
            ttl=12 * 60 * 60,
            cache_group=cache_group,
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
            forecast_url,
            headers=WEATHER_GOV_HEADERS,
            ttl=10 * 60,
            cache_group=cache_group,
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
    hourly_periods = []
    if hourly_url:
        try:
            hourly_data = cached_get_json(
                hourly_url,
                headers=WEATHER_GOV_HEADERS,
                ttl=10 * 60,
                cache_group=cache_group,
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
            alerts_url,
            headers=WEATHER_GOV_HEADERS,
            ttl=5 * 60,
            cache_group=cache_group,
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

    if location_key:
        register_location(location_key, location, lat, lon)

    current_temp = periods[0].get("temperature")
    current_unit = periods[0].get("temperatureUnit")
    humidity_value = None
    wind_speed_mph = _parse_wind_speed_mph(periods[0].get("windSpeed"))

    if hourly_periods:
        hourly_current = hourly_periods[0]
        hourly_temp = hourly_current.get("temperature")
        hourly_unit = hourly_current.get("temperatureUnit") or current_unit
        if hourly_temp is not None:
            current_temp = hourly_temp
            current_unit = hourly_unit
        humidity = (hourly_current.get("relativeHumidity") or {}).get("value")
        try:
            humidity_value = float(humidity) if humidity is not None else None
        except (TypeError, ValueError):
            humidity_value = None
        wind_speed_mph = _parse_wind_speed_mph(hourly_current.get("windSpeed")) or wind_speed_mph

    feels_like_temp = _calculate_feels_like(
        current_temp, current_unit, humidity_value, wind_speed_mph
    )
    if feels_like_temp is None:
        feels_like_temp = current_temp

    return {
        "location": location,
        "period": periods[0],
        "next_period": periods[1] if len(periods) > 1 else None,
        "hourly_today": hourly_today,
        "hourly_error": hourly_error,
        "daily_forecast": build_daily_forecast(periods),
        "alerts": alerts,
        "alerts_error": alerts_error,
        "feels_like_temperature": feels_like_temp,
        "feels_like_unit": current_unit,
        "actual_temperature": current_temp,
        "actual_temperature_unit": current_unit,
    }, None
