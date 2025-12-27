import json
import os
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode

import requests

DEFAULT_USER_AGENT = "(weather.jawand.dev, jawandsingh@gmail.com)"
CACHE_FILE = os.getenv(
    "WEATHER_CACHE_FILE", os.path.join(os.path.dirname(__file__), "weather_cache.json")
)
CACHE_LOCK = Lock()


def get_weather_headers():
    user_agent = os.getenv("WEATHER_GOV_USER_AGENT", DEFAULT_USER_AGENT)
    return {
        "User-Agent": user_agent,
        "Accept": "application/geo+json",
    }


def get_geocoder_headers():
    user_agent = os.getenv("WEATHER_GOV_USER_AGENT", DEFAULT_USER_AGENT)
    return {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Accept-Language": "en",
    }


def _cache_key(url, params):
    if not params:
        return url
    query = urlencode(sorted(params.items(), key=lambda item: item[0]), doseq=True)
    return f"{url}?{query}"


def _load_cache_file():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_cache_file(cache):
    cache_dir = os.path.dirname(CACHE_FILE)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    temp_path = f"{CACHE_FILE}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(cache, handle)
        os.replace(temp_path, CACHE_FILE)
    except OSError:
        return


def _prune_cache(cache, now):
    for key in list(cache.keys()):
        entry = cache.get(key, {})
        if entry.get("expires_at", 0) <= now:
            cache.pop(key, None)


def cached_get_json(url, *, headers=None, params=None, timeout=10, ttl=600):
    cache_key = _cache_key(url, params)
    now = time.time()
    with CACHE_LOCK:
        cache = _load_cache_file()
        cached = cache.get(cache_key)
        if cached and cached.get("expires_at", 0) > now:
            return cached.get("value")

    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    with CACHE_LOCK:
        cache = _load_cache_file()
        write_time = time.time()
        _prune_cache(cache, write_time)
        cache[cache_key] = {"expires_at": write_time + ttl, "value": data}
        _write_cache_file(cache)
    return data


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_hour_label(dt):
    if not dt:
        return None
    return dt.strftime("%I %p").lstrip("0")


def format_alert_time(value):
    dt = parse_iso_datetime(value)
    if not dt:
        return None
    return dt.strftime("%a %I:%M %p").lstrip("0")
