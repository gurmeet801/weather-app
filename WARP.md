# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A Flask + Tailwind CSS weather application that displays forecasts for US locations using the National Weather Service API (api.weather.gov) and OpenStreetMap Nominatim for geocoding.

## Commands

### Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run Development Server
```powershell
python app.py
```
Server runs at http://127.0.0.1:4200

### Required Environment Variables
The `.env` file must contain:
- `WEATHER_GOV_USER_AGENT` - Required User-Agent header for weather.gov and Nominatim APIs (e.g., `"weather-app (you@example.com)"`)
- `WEATHER_CACHE_FILE` - Path to JSON cache file (e.g., `"artifacts/weather_cache.json"`)
- `DEFAULT_LOCATION` - Default location when no query provided (e.g., `"16066"` or `"City, State"`)
- `WEATHER_APP_PORT` - Server port (default: `4200`)

### Deployment Scripts (Windows)
- `scripts\Install-WeatherApp.ps1` - Install as Windows service
- `scripts\Restart-WeatherApp.ps1` - Restart service
- `scripts\warm-ping.ps1` - Warm cache for default location
- `scripts\Install-WarmPing.ps1` - Schedule warm-ping task

## Architecture

### Entry Point
`app.py` - Flask application with routes:
- `/` - Main page with weather display
- `/api/extras` - Lazy-loaded hourly forecast, alerts, and detailed data
- `/refresh` - Clear/delete location cache
- `/warm` - Pre-warm cache for default location

### Services Layer (`services/`)
- `geocode_service.py` - Geocoding via Nominatim API. Handles ZIP codes and addresses. Includes throttling (1 req/sec minimum) per Nominatim policy.
- `weather_service.py` - Weather data from api.weather.gov. Fetches forecasts, hourly data, alerts, and observations. Contains complex alert zone distance calculations and feels-like temperature logic.

### Utilities (`utils.py`)
- JSON file-based caching with TTL and daily auto-expiration
- Location aliasing system (coordinates → canonical "City, State" keys)
- Cache groups per location for isolated invalidation
- Thread-safe cache operations via `CACHE_LOCK`
- Auto-loads `.env` file at import time

### Frontend
- `templates/` - Jinja2 templates with component partials in `templates/components/`
- `static/styles.css` - Tailwind CSS (pre-compiled)
- `static/js/weather.js` - Client-side logic for geolocation, lazy loading extras, modals
- `static/sw.js` - Service worker for PWA offline support
- Asset versioning via file mtime for cache busting

### Caching Strategy
Weather data is cached in a JSON file organized by:
1. **Groups**: Location-specific cache buckets (keyed by `loc:City, State`)
2. **Aliases**: Maps coordinate strings and addresses to canonical location keys
3. **Daily refresh**: Entire cache clears at midnight

API TTLs:
- Points API: 5 minutes
- Forecasts: 5 minutes  
- Hourly: 5 minutes
- Stations list: 6 hours
- Observations: 1 minute
- Geocoding: 24 hours
- Alert zones: 24 hours

## Key Patterns

### Location Resolution
Coordinates are mapped to canonical "City, State" keys via aliases. This allows cache sharing when the same location is accessed via different coordinates, ZIP codes, or addresses.

### Deferred Loading
The main page can defer hourly/alert data (`defer_extras=True`) for faster initial load. The `/api/extras` endpoint fetches remaining data.

### External API Rate Limiting
Nominatim requires 1 second minimum between requests - enforced via `_throttle_nominatim()` with a global lock.
