"""
Test if stale cache data could persist
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import os
import json
import time
from utils import CACHE_FILE, clear_location_cache, _load_cache_file

print("=" * 70)
print("TESTING STALE CACHE ISSUE")
print("=" * 70)

# First populate cache with initial data
from services.weather_service import fetch_forecast

lat, lon = 40.6870, -80.0709
print(f"\nFetching forecast for {lat}, {lon}")
forecast1, _ = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)
print(f"Got location: {forecast1['location_key']}")
print(f"Tonight temp: {forecast1['period']['temperature']}°F")

# Check what's cached
print("\nCache contents after first fetch:")
cache = _load_cache_file()
for group_key in cache.get('groups', {}).keys():
    print(f"  - {group_key}")

# Now clear ONLY the location cache (like the refresh endpoint does)
location_key = forecast1['location_key']
print(f"\nClearing location cache for: {location_key}")
clear_location_cache(location_key)

# Check what's left
print("\nCache contents after location clear:")
cache = _load_cache_file()
for group_key in cache.get('groups', {}).keys():
    print(f"  - {group_key}")

# Fetch again - this should get fresh data
print(f"\nFetching forecast again (should be fresh)...")
forecast2, _ = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)
print(f"Tonight temp: {forecast2['period']['temperature']}°F")

# Now test the points_api cache
print("\n" + "=" * 70)
print("TESTING POINTS_API CACHE")
print("=" * 70)

# Check if points_api has cached data
if 'points_api' in cache.get('groups', {}):
    points_cache = cache['groups']['points_api']
    print(f"Points API cache has {len(points_cache)} entries")
    for key in list(points_cache.keys())[:3]:
        print(f"  - {key[:80]}...")
        
# The issue might be that points_api caches the grid X,Y coordinates
# and if the grid changes, we might get stale data

print("\n" + "=" * 70)
print("CHECKING FOR GRID MISMATCH")
print("=" * 70)

# Get fresh points data
import requests
headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

print(f"\nLive API grid: {props['gridId']}/{props['gridX']},{props['gridY']}")
print(f"Forecast URL: {props['forecast']}")

# Check if this matches cached
for key in points_cache.keys():
    if lat in key and lon in key:
        print(f"\nCached points URL: {key}")
        cached_data = points_cache[key].get('value', {})
        cached_props = cached_data.get('properties', {})
        if 'gridX' in cached_props:
            print(f"Cached grid: {cached_props.get('gridId')}/{cached_props.get('gridX')},{cached_props.get('gridY')}")
        break

print("\n" + "=" * 70)
print("STALE CACHE TEST COMPLETE")
print("=" * 70)
