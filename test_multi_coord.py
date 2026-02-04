"""
Test what happens with different coordinates for same area
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import fetch_forecast
import json
import os

CACHE_FILE = r'y:\weather-app\artifacts\weather_cache.json'

print("=" * 70)
print("TESTING MULTIPLE COORDINATES FOR SAME AREA")
print("=" * 70)

# Clear cache first
if os.path.exists(CACHE_FILE):
    os.remove(CACHE_FILE)
    print("Cleared cache")

# Test with different coordinates for Seven Fields / Cranberry area
coord_tests = [
    (40.6870, -80.0709, "Seven Fields center"),
    (40.6941, -80.1201, "Cranberry Twp (ZIP 16066)"),
]

for lat, lon, desc in coord_tests:
    print(f"\n{'='*70}")
    print(f"Testing: {desc}")
    print(f"Coordinates: {lat}, {lon}")
    print(f"{'='*70}")
    
    forecast, error = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)
    
    if error:
        print(f"Error: {error}")
    else:
        print(f"Location: {forecast['location']}")
        print(f"Location Key: {forecast['location_key']}")
        print(f"Period temp: {forecast['period']['temperature']} {forecast['period']['temperatureUnit']}")
    
    # Check cache after each call
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        print(f"\nCache locations: {list(cache.get('locations', {}).keys())}")
        print(f"Cache groups: {list(cache.get('groups', {}).keys())}")
        print(f"Cache aliases: {list(cache.get('aliases', {}).keys())}")

print("\n" + "=" * 70)
print("FINAL CACHE STATE")
print("=" * 70)

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    print("\nAll locations:")
    for loc_key, loc_data in cache.get('locations', {}).items():
        print(f"  - {loc_key}: {loc_data.get('lat')}, {loc_data.get('lon')}")
    
    print("\nAll groups:")
    for group_key in cache.get('groups', {}).keys():
        print(f"  - {group_key}")
    
    print("\nAll aliases:")
    for alias_key, canonical in cache.get('aliases', {}).items():
        print(f"  - {alias_key} -> {canonical}")
