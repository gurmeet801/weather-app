import math
import re
from datetime import datetime
from urllib.parse import urlparse

import requests

from services.geocode_service import geocode_place
from utils import (
    cached_get_json,
    format_location_key,
    format_coordinate_alias,
    format_alert_time,
    format_hour_label,
    get_weather_headers,
    location_group_key,
    parse_iso_datetime,
    register_location,
    register_location_alias,
    resolve_location_alias,
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


ALERT_AREA_BASE_COLORS = {
    "minor": (29, 78, 216),
    "moderate": (180, 83, 9),
    "severe": (185, 28, 28),
    "extreme": (127, 29, 29),
}

ALERT_AREA_LIGHTEN_MAX = 0.72


def _haversine_miles(lat1, lon1, lat2, lon2):
    radius = 3959
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def _zone_id_from_url(url):
    if not url:
        return None
    try:
        path = urlparse(url).path
    except Exception:
        path = str(url)
    parts = [part for part in path.split("/") if part]
    return parts[-1] if parts else None


def _polygon_centroid_with_area(points):
    if not points or len(points) < 3:
        return None, 0
    if points[0] != points[-1]:
        points = points + [points[0]]
    area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        cross = (x0 * y1) - (x1 * y0)
        area += cross
        centroid_x += (x0 + x1) * cross
        centroid_y += (y0 + y1) * cross
    if area == 0:
        return None, 0
    area *= 0.5
    centroid_x /= (6 * area)
    centroid_y /= (6 * area)
    return (centroid_y, centroid_x), abs(area)


def _geometry_centroid(geometry):
    if not geometry or not isinstance(geometry, dict):
        return None, None
    geometry_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if not coords:
        return None, None
    if geometry_type == "Point":
        if len(coords) < 2:
            return None, None
        return coords[1], coords[0]
    if geometry_type == "Polygon":
        centroid, _ = _polygon_centroid_with_area(coords[0])
        if centroid:
            return centroid[0], centroid[1]
        return None, None
    if geometry_type == "MultiPolygon":
        total_area = 0.0
        sum_x = 0.0
        sum_y = 0.0
        for polygon in coords:
            if not polygon:
                continue
            centroid, area = _polygon_centroid_with_area(polygon[0])
            if not centroid or area == 0:
                continue
            lat, lon = centroid
            sum_x += lon * area
            sum_y += lat * area
            total_area += area
        if total_area:
            return sum_y / total_area, sum_x / total_area
        return None, None
    return None, None


def _zone_center_from_properties(properties):
    if not properties:
        return None, None
    center = properties.get("center")
    if isinstance(center, dict) and center.get("type") == "Point":
        coords = center.get("coordinates") or []
        if len(coords) >= 2:
            return coords[1], coords[0]
    lat = properties.get("latitude") or properties.get("lat")
    lon = properties.get("longitude") or properties.get("lon")
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (TypeError, ValueError):
            return None, None
    return None, None


def _fetch_alert_zone(zone_url):
    if not zone_url:
        return None
    try:
        return cached_get_json(
            zone_url,
            headers=WEATHER_GOV_HEADERS,
            ttl=24 * 60 * 60,
            cache_group="alert_zones",
        )
    except requests.HTTPError:
        return None
    except requests.RequestException:
        return None


def _split_area_desc(area_desc):
    if not area_desc:
        return []
    parts = [part.strip() for part in area_desc.split(";") if part.strip()]
    if len(parts) <= 1:
        parts = [part.strip() for part in re.split(r",\s*", area_desc) if part.strip()]
    seen = set()
    unique = []
    for part in parts:
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(part)
    return unique


def _area_query_variants(area_name):
    cleaned = area_name.strip()
    if not cleaned:
        return []
    lowered = cleaned.lower()
    if any(
        token in lowered
        for token in ("county", "parish", "borough", "city", "district", "zone")
    ):
        return [cleaned]
    return [cleaned, f"{cleaned} County"]


def _shade_from_base(base_color, ratio, max_lighten=ALERT_AREA_LIGHTEN_MAX):
    if not base_color:
        base_color = ALERT_AREA_BASE_COLORS["minor"]
    base_r, base_g, base_b = base_color
    clamped = max(0, min(1, ratio))
    t = clamped * max_lighten
    r = round(base_r + (255 - base_r) * t)
    g = round(base_g + (255 - base_g) * t)
    b = round(base_b + (255 - base_b) * t)
    return r, g, b


def _text_color_for_rgb(r, g, b):
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "#1a1a1a" if luminance > 0.6 else "#ffffff"


def _build_alert_areas(
    area_desc,
    origin_lat,
    origin_lon,
    severity_slug=None,
    affected_zones=None,
):
    try:
        origin_lat = float(origin_lat)
        origin_lon = float(origin_lon)
    except (TypeError, ValueError):
        origin_lat = None
        origin_lon = None

    areas = []
    geocode_cache = {}
    zone_cache = {}

    if affected_zones:
        for zone_url in affected_zones:
            if not zone_url:
                continue
            zone_data = zone_cache.get(zone_url)
            if zone_data is None:
                zone_data = _fetch_alert_zone(zone_url)
                zone_cache[zone_url] = zone_data
            if not zone_data:
                continue
            props = zone_data.get("properties", {}) or {}
            name = props.get("name") or props.get("id") or _zone_id_from_url(zone_url) or zone_url
            state = props.get("state")
            display_name = name
            if state and state not in name:
                display_name = f"{name}, {state}"
            zone_id = props.get("id") or zone_data.get("id") or _zone_id_from_url(zone_url)

            lat, lon = _geometry_centroid(zone_data.get("geometry"))
            if lat is None or lon is None:
                lat, lon = _zone_center_from_properties(props)
            if lat is None or lon is None:
                cache_key = display_name.lower()
                lat, lon = geocode_cache.get(cache_key, (None, None))
                if lat is None or lon is None:
                    lat, lon = geocode_place(display_name)
                geocode_cache[cache_key] = (lat, lon)

            distance = None
            if origin_lat is not None and origin_lon is not None and lat is not None and lon is not None:
                distance = _haversine_miles(origin_lat, origin_lon, lat, lon)

            areas.append(
                {
                    "name": display_name,
                    "distance": distance,
                    "distance_mi": int(round(distance)) if distance is not None else None,
                    "color": None,
                    "text_color": None,
                    "is_closest": False,
                    "zone_id": zone_id,
                    "state": state,
                }
            )

        if areas:
            deduped = []
            seen = set()
            for area in areas:
                key = area.get("zone_id") or area["name"].lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(area)
            areas = deduped

    if not areas:
        area_names = _split_area_desc(area_desc)
        if not area_names:
            return []
        for name in area_names:
            cache_key = name.lower()
            lat, lon = geocode_cache.get(cache_key, (None, None))
            if lat is None or lon is None:
                for query in _area_query_variants(name):
                    lat, lon = geocode_place(query)
                    if lat is not None and lon is not None:
                        break
            geocode_cache[cache_key] = (lat, lon)

            distance = None
            if (
                origin_lat is not None
                and origin_lon is not None
                and lat is not None
                and lon is not None
            ):
                distance = _haversine_miles(origin_lat, origin_lon, lat, lon)

            areas.append(
                {
                    "name": name,
                    "distance": distance,
                    "distance_mi": int(round(distance)) if distance is not None else None,
                    "color": None,
                    "text_color": None,
                    "is_closest": False,
                }
            )

    base_color = ALERT_AREA_BASE_COLORS.get(severity_slug, ALERT_AREA_BASE_COLORS["minor"])
    distances = [area["distance"] for area in areas if area["distance"] is not None]
    min_distance = min(distances) if distances else None
    max_distance = max(distances) if distances else None
    if distances and min_distance is not None and max_distance is not None:
        for area in areas:
            if area["distance"] is None:
                continue
            ratio = 0 if max_distance == min_distance else (
                (area["distance"] - min_distance) / (max_distance - min_distance)
            )
            r, g, b = _shade_from_base(base_color, ratio)
            area["color"] = f"rgb({r}, {g}, {b})"
            area["text_color"] = _text_color_for_rgb(r, g, b)
            if abs(area["distance"] - min_distance) < 0.25:
                area["is_closest"] = True

    areas.sort(key=lambda item: (item["distance"] is None, item["distance"] or 0))
    return areas


def _severity_slug(value):
    if not value:
        return "minor"
    lowered = value.strip().lower()
    if lowered in ("minor", "moderate", "severe", "extreme"):
        return lowered
    return "minor"


def _alert_base_title(props):
    if not props:
        return "Weather Alert"
    event = props.get("event")
    if event:
        title = str(event).strip()
        return title or "Weather Alert"
    headline = props.get("headline") or ""
    cleaned = str(headline).strip()
    lowered = cleaned.lower()
    for token in (" issued ", " until ", " by "):
        idx = lowered.find(token)
        if idx != -1:
            cleaned = cleaned[:idx].strip()
            break
    return cleaned or "Weather Alert"


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


def build_hourly_today(periods, limit=24):
    if not periods or limit <= 0:
        return []
    hourly = []
    for period in periods:
        dt = parse_iso_datetime(period.get("startTime"))
        if not dt:
            continue
        hourly.append(
            {
                "time": format_hour_label(dt),
                "temperature": period.get("temperature"),
                "temperatureUnit": period.get("temperatureUnit"),
                "shortForecast": period.get("shortForecast"),
            }
        )
        if len(hourly) >= limit:
            break
    return hourly


def build_daily_forecast(periods, limit=7):
    if not periods:
        return []
    grouped = {}
    order = []
    today = None

    for period in periods:
        dt = parse_iso_datetime(period.get("startTime"))
        if not dt:
            continue
        if today is None:
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            today = now.date()
        if today and dt.date() < today:
            continue
        day_key = dt.date().isoformat()
        if day_key not in grouped:
            grouped[day_key] = {
                "date": dt,
                "key": day_key,
                "date_label": dt.strftime("%a, %b %d"),
                "name": dt.strftime("%a"),
                "shortForecast": None,
                "high": None,
                "low": None,
                "all_high": None,
                "all_low": None,
                "temperatureUnit": period.get("temperatureUnit"),
            }
            order.append(day_key)

        entry = grouped[day_key]
        temp = period.get("temperature")
        if isinstance(temp, (int, float)):
            entry["all_high"] = (
                temp if entry["all_high"] is None else max(entry["all_high"], temp)
            )
            entry["all_low"] = (
                temp if entry["all_low"] is None else min(entry["all_low"], temp)
            )
            if period.get("isDaytime"):
                entry["high"] = temp if entry["high"] is None else max(entry["high"], temp)
            else:
                entry["low"] = temp if entry["low"] is None else min(entry["low"], temp)
        if period.get("isDaytime"):
            entry["name"] = period.get("name") or entry["name"]
            if period.get("shortForecast"):
                entry["shortForecast"] = period.get("shortForecast")
        else:
            if entry.get("name") == dt.strftime("%a") and period.get("name"):
                entry["name"] = period.get("name")
            if entry.get("shortForecast") is None and period.get("shortForecast"):
                entry["shortForecast"] = period.get("shortForecast")
        if entry.get("temperatureUnit") is None and period.get("temperatureUnit"):
            entry["temperatureUnit"] = period.get("temperatureUnit")

    daily = []
    for day_key in order[:limit]:
        entry = grouped[day_key]
        high = entry.get("high") if entry.get("high") is not None else entry.get("all_high")
        low = entry.get("low") if entry.get("low") is not None else entry.get("all_low")
        daily.append(
            {
                "key": entry.get("key"),
                "date_label": entry.get("date_label"),
                "name": entry.get("name") or entry["date"].strftime("%a"),
                "shortForecast": entry.get("shortForecast"),
                "high": high,
                "low": low,
                "temperatureUnit": entry.get("temperatureUnit"),
            }
        )
    return daily


def build_daily_details(periods, limit=7):
    if not periods:
        return []
    grouped = {}
    order = []
    today = None

    for period in periods:
        dt = parse_iso_datetime(period.get("startTime"))
        if not dt:
            continue
        if today is None:
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            today = now.date()
        if today and dt.date() < today:
            continue

        day_key = dt.date().isoformat()
        if day_key not in grouped:
            grouped[day_key] = {
                "key": day_key,
                "date_label": dt.strftime("%a, %b %d"),
                "hours": [],
            }
            order.append(day_key)

        temp = period.get("temperature")
        unit = period.get("temperatureUnit")
        temp_value = temp if isinstance(temp, (int, float)) else None
        humidity = (period.get("relativeHumidity") or {}).get("value")
        try:
            humidity_value = float(humidity) if humidity is not None else None
        except (TypeError, ValueError):
            humidity_value = None
        wind_mph = _parse_wind_speed_mph(period.get("windSpeed"))
        feels_like = _calculate_feels_like(temp_value, unit, humidity_value, wind_mph)
        precip = (period.get("probabilityOfPrecipitation") or {}).get("value")
        try:
            precip_value = float(precip) if precip is not None else None
        except (TypeError, ValueError):
            precip_value = None

        grouped[day_key]["hours"].append(
            {
                "time": format_hour_label(dt),
                "hour": dt.hour,
                "temperature": temp_value,
                "temperatureUnit": unit,
                "feelsLike": feels_like,
                "precipChance": precip_value,
                "shortForecast": period.get("shortForecast"),
            }
        )

    daily = []
    for day_key in order[:limit]:
        daily.append(grouped[day_key])
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

    # Create coordinate alias
    coord_alias = format_coordinate_alias(lat, lon)
    
    # Check if we already have a canonical location for these coordinates
    cached_location_key = resolve_location_alias(coord_alias)
    
    points_url = f"https://api.weather.gov/points/{lat},{lon}"

    try:
        # Use a temporary cache group for the points API call to get city/state
            points_data = cached_get_json(
                points_url,
                headers=WEATHER_GOV_HEADERS,
                ttl=5 * 60,
                cache_group="points_api",
            )
    except requests.HTTPError:
        return None, "Weather.gov returned an error for those coordinates."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    points_props = points_data.get("properties", {})
    time_zone = points_props.get("timeZone")
    forecast_url = points_props.get("forecast")
    hourly_url = points_props.get("forecastHourly")
    if not forecast_url:
        return None, "No forecast URL available for that location."

    # Extract city and state to create canonical location key
    location_props = (
        points_props.get("relativeLocation", {}).get("properties", {}) or {}
    )
    city = location_props.get("city")
    state = location_props.get("state")
    
    if not city or not state:
        return None, "Could not determine city and state for this location."
    
    # Create canonical location key from City, State
    location_key = format_location_key(city, state)
    location = f"{city}, {state}"
    
    # Register the coordinate alias to point to the canonical location
    if coord_alias and location_key and (not cached_location_key or cached_location_key != location_key):
        register_location_alias(coord_alias, location_key)
    
    # Use the canonical location key for caching
    cache_group = location_group_key(location_key)

    try:
        forecast_data = cached_get_json(
            forecast_url,
            headers=WEATHER_GOV_HEADERS,
            ttl=5 * 60,
            cache_group=cache_group,
        )
    except requests.HTTPError:
        return None, "Weather.gov returned an error for the forecast request."
    except requests.RequestException:
        return None, "Could not reach api.weather.gov."

    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        return None, "No forecast periods available for that location."

    hourly_today = []
    hourly_error = None
    hourly_periods = []
    daily_details = []
    if hourly_url:
        try:
            hourly_data = cached_get_json(
                hourly_url,
                headers=WEATHER_GOV_HEADERS,
                ttl=5 * 60,
                cache_group=cache_group,
            )
            hourly_periods = hourly_data.get("properties", {}).get("periods", [])
            hourly_today = build_hourly_today(hourly_periods)
            daily_details = build_daily_details(hourly_periods)
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
            start_time = props.get("onset")
            end_time = props.get("ends")
            area_desc = props.get("areaDesc")
            severity = props.get("severity")
            severity_slug = _severity_slug(severity)
            issued_time = format_alert_time(props.get("sent"))
            issuer = props.get("senderName")
            base_title = _alert_base_title(props)
            long_sentence = base_title
            if issued_time:
                long_sentence = f"{long_sentence} issued {issued_time}"
            if issuer:
                long_sentence = f"{long_sentence} by {issuer}"
            alerts.append(
                {
                    "title": long_sentence,
                    "event": base_title,
                    "severity": severity,
                    "severity_slug": severity_slug,
                    "area": area_desc,
                    "areas": _build_alert_areas(
                        area_desc,
                        lat,
                        lon,
                        severity_slug,
                        props.get("affectedZones"),
                    ),
                    "issuer": issuer,
                    "sent": issued_time,
                    "start_iso": start_time,
                    "end_iso": end_time,
                    "start": format_alert_time(start_time),
                    "ends": format_alert_time(end_time),
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
    precip_value = None
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
        precip = (hourly_current.get("probabilityOfPrecipitation") or {}).get("value")
        try:
            precip_value = float(precip) if precip is not None else None
        except (TypeError, ValueError):
            precip_value = None
        wind_speed_mph = _parse_wind_speed_mph(hourly_current.get("windSpeed")) or wind_speed_mph

    feels_like_temp = _calculate_feels_like(
        current_temp, current_unit, humidity_value, wind_speed_mph
    )
    if feels_like_temp is None:
        feels_like_temp = current_temp

    humidity_percent = (
        int(round(humidity_value)) if isinstance(humidity_value, (int, float)) else None
    )
    precip_percent = (
        int(round(precip_value)) if isinstance(precip_value, (int, float)) else None
    )

    return {
        "location": location,
        "period": periods[0],
        "next_period": periods[1] if len(periods) > 1 else None,
        "hourly_today": hourly_today,
        "hourly_error": hourly_error,
        "daily_details": daily_details,
        "daily_forecast": build_daily_forecast(periods),
        "alerts": alerts,
        "alerts_error": alerts_error,
        "feels_like_temperature": feels_like_temp,
        "feels_like_unit": current_unit,
        "actual_temperature": current_temp,
        "actual_temperature_unit": current_unit,
        "humidity": humidity_percent,
        "precip_chance": precip_percent,
        "location_key": location_key,
        "time_zone": time_zone,
    }, None
