"""
Test the refresh endpoint behavior
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import os
import json
import time
from utils import CACHE_FILE, clear_cache, clear_location_cache

print("=" * 70)
print("TESTING REFRESH ENDPOINT BEHAVIOR")
print("=" * 70)

# First populate the cache
from services.weather_service import fetch_forecast
lat, lon = 40.6870, -80.0709
forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error fetching forecast: {error}")
    sys.exit(1)

print(f"\nCache populated with location: {forecast['location_key']}")

# Check cache size before
if os.path.exists(CACHE_FILE):
    size_before = os.path.getsize(CACHE_FILE)
    with open(CACHE_FILE, 'r') as f:
        cache_before = json.load(f)
    print(f"Cache file size: {size_before} bytes")
    print(f"Cache groups: {list(cache_before.get('groups', {}).keys())}")

# Test 1: Clear specific location cache
print("\n" + "=" * 70)
print("TEST 1: Clear location-specific cache")
print("=" * 70)

location_key = forecast['location_key']
print(f"Clearing cache for: {location_key}")
clear_location_cache(location_key)

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache_after = json.load(f)
    group_key = f"loc:{location_key}"
    if group_key in cache_after.get('groups', {}):
        print(f"ERROR: Group {group_key} still exists!")
    else:
        print(f"SUCCESS: Group {group_key} was removed")
else:
    print("Cache file was deleted (unexpected for location-only clear)")

# Test 2: Full cache clear
print("\n" + "=" * 70)
print("TEST 2: Full cache clear")
print("=" * 70)

# Repopulate first
forecast, _ = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)
print(f"Cache repopulated")

print(f"Cache exists before clear: {os.path.exists(CACHE_FILE)}")
clear_cache()
print(f"Cache exists after clear: {os.path.exists(CACHE_FILE)}")

if os.path.exists(CACHE_FILE):
    print("ERROR: Cache file still exists after clear_cache()!")
else:
    print("SUCCESS: Cache file was deleted")

# Test 3: Check if cache gets recreated immediately
print("\n" + "=" * 70)
print("TEST 3: Check for immediate cache recreation")
print("=" * 70)

# Fetch again - this should create new cache
forecast, _ = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)
print(f"Fetched forecast after clear")
print(f"Cache exists: {os.path.exists(CACHE_FILE)}")

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache_new = json.load(f)
    print(f"New cache groups: {list(cache_new.get('groups', {}).keys())}")

# Test 4: Multiple rapid clears
print("\n" + "=" * 70)
print("TEST 4: Multiple rapid clears")
print("=" * 70)

for i in range(3):
    clear_cache()
    print(f"Clear {i+1}: Cache exists = {os.path.exists(CACHE_FILE)}")
    time.sleep(0.1)

print("\n" + "=" * 70)
print("CACHE CLEAR TESTS COMPLETE")
print("=" * 70)
