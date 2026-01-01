import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from urllib.parse import urlencode

import requests

def _load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_env()


def _resolve_cache_path(cache_path):
    if not cache_path:
        return cache_path
    try:
        path = Path(cache_path)
    except TypeError:
        return cache_path
    if path.is_absolute():
        return str(path)
    repo_root = Path(__file__).resolve().parent
    return str((repo_root / path).resolve())


_LOGGER = logging.getLogger(__name__)


def _required_env(name):
    value = os.getenv(name)
    if not value:
        _LOGGER.error("Required environment variable %s is not set. Add it to .env.", name)
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


USER_AGENT = _required_env("WEATHER_GOV_USER_AGENT")
CACHE_FILE = _resolve_cache_path(_required_env("WEATHER_CACHE_FILE"))
CACHE_LOCK = Lock()


def get_weather_headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }


def get_geocoder_headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en",
    }


def format_location_key(city, state):
    """Create a canonical location key from City, State."""
    if not city or not state:
        return None
    # Normalize to "City, State" format
    city = city.strip()
    state = state.strip()
    return f"{city}, {state}"


def format_coordinate_alias(lat_value, lon_value):
    """Create an alias key from lat/lon coordinates."""
    try:
        lat = float(lat_value)
        lon = float(lon_value)
    except (TypeError, ValueError):
        return None
    return f"coord:{lat:.4f},{lon:.4f}"


def resolve_location_alias(alias_key):
    """Resolve an alias (coordinates, zip, etc.) to canonical City, State location key."""
    if not alias_key:
        return None
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        aliases = cache.get("aliases", {})
        return aliases.get(alias_key)


def register_location_alias(alias_key, canonical_key):
    """Register an alias (coordinates, zip, etc.) to point to canonical City, State location."""
    if not alias_key or not canonical_key:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        if "aliases" not in cache:
            cache["aliases"] = {}
        cache["aliases"][alias_key] = canonical_key
        _write_cache_file(cache)


def location_group_key(location_key):
    if not location_key:
        return "default"
    return f"loc:{location_key}"


def _cache_key(url, params):
    if not params:
        return url
    query = urlencode(sorted(params.items(), key=lambda item: item[0]), doseq=True)
    return f"{url}?{query}"


def _today_key():
    return datetime.now().date().isoformat()


def _empty_cache():
    return {"meta": {"last_refresh_date": _today_key()}, "groups": {}, "locations": {}, "aliases": {}}


def _normalize_cache(raw_cache):
    if not isinstance(raw_cache, dict):
        return _empty_cache()
    if "groups" not in raw_cache:
        raw_cache = {"meta": {}, "groups": {"default": raw_cache}, "locations": {}, "aliases": {}}
    raw_cache.setdefault("meta", {})
    raw_cache.setdefault("locations", {})
    raw_cache.setdefault("groups", {})
    raw_cache.setdefault("aliases", {})
    if not isinstance(raw_cache.get("groups"), dict):
        raw_cache["groups"] = {}
    if not isinstance(raw_cache.get("locations"), dict):
        raw_cache["locations"] = {}
    if not isinstance(raw_cache.get("aliases"), dict):
        raw_cache["aliases"] = {}
    return raw_cache


def _ensure_today(cache):
    today = _today_key()
    if cache.get("meta", {}).get("last_refresh_date") != today:
        cache["groups"] = {}
        cache["locations"] = {}
        cache["aliases"] = {}
        cache["meta"]["last_refresh_date"] = today
        return True
    return False


def _load_cache_file():
    if not os.path.exists(CACHE_FILE):
        return _empty_cache()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return _normalize_cache(data)
    except (OSError, json.JSONDecodeError):
        return _empty_cache()


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


def _prune_group_cache(group_cache, now):
    for key in list(group_cache.keys()):
        entry = group_cache.get(key, {})
        if entry.get("expires_at", 0) <= now:
            group_cache.pop(key, None)


def cached_get_json(
    url,
    *,
    headers=None,
    params=None,
    timeout=10,
    ttl=600,
    cache_group="default",
    throttle=None,
):
    cache_key = _cache_key(url, params)
    now = time.time()
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        group_cache = cache.get("groups", {}).get(cache_group, {})
        cached = group_cache.get(cache_key)
        if cached and cached.get("expires_at", 0) > now:
            return cached.get("value")

    if throttle:
        throttle()
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        group_cache = cache.get("groups", {}).setdefault(cache_group, {})
        write_time = time.time()
        _prune_group_cache(group_cache, write_time)
        group_cache[cache_key] = {"expires_at": write_time + ttl, "value": data}
        cache["groups"][cache_group] = group_cache
        _write_cache_file(cache)
    return data


def clear_cache():
    with CACHE_LOCK:
        for path in (CACHE_FILE, f"{CACHE_FILE}.tmp"):
            try:
                os.remove(path)
            except FileNotFoundError:
                continue
            except OSError:
                continue


def register_location(location_key, label, lat, lon):
    if not location_key:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache["locations"][location_key] = {
            "label": label or location_key,
            "lat": float(lat),
            "lon": float(lon),
            "updated_at": int(time.time()),
        }
        _write_cache_file(cache)


def list_cached_locations():
    with CACHE_LOCK:
        cache = _load_cache_file()
        changed = _ensure_today(cache)
        locations = []
        for key, value in cache.get("locations", {}).items():
            if not isinstance(value, dict):
                continue
            label = str(value.get("label") or key)
            locations.append(
                {
                    "key": key,
                    "label": label,
                    "lat": value.get("lat"),
                    "lon": value.get("lon"),
                }
            )
        if changed:
            _write_cache_file(cache)
    return sorted(locations, key=lambda item: item["label"].lower())


def clear_cache_group(cache_group):
    if not cache_group:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache.get("groups", {}).pop(cache_group, None)
        _write_cache_file(cache)


def clear_location_cache(location_key):
    if not location_key:
        return
    clear_cache_group(location_group_key(location_key))


def delete_location_cache(location_key):
    if not location_key:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache.get("groups", {}).pop(location_group_key(location_key), None)
        cache.get("locations", {}).pop(location_key, None)
        _write_cache_file(cache)


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
    hour = dt.strftime("%I").lstrip("0")
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p").lower()
    return f"{hour}:{minute}{ampm}"


def format_alert_time(value):
    dt = parse_iso_datetime(value)
    if not dt:
        return None
    return format_display_datetime(dt)


def format_display_datetime(dt):
    if not dt:
        return None
    hour = dt.strftime("%I").lstrip("0")
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p").lower()
    return f"{dt.strftime('%a')}, {dt.strftime('%m/%d')}, {hour}:{minute}{ampm}"
