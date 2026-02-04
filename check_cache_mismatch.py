"""
Check for cache key mismatches
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import json
import os

CACHE_FILE = r'y:\weather-app\artifacts\weather_cache.json'

print("=" * 70)
print("CHECKING FOR CACHE KEY MISMATCHES")
print("=" * 70)

if not os.path.exists(CACHE_FILE):
    print("No cache file found")
    sys.exit(0)

with open(CACHE_FILE, 'r') as f:
    cache = json.load(f)

print("\nLocations in cache:")
for loc_key, loc_data in cache.get('locations', {}).items():
    print(f"  - {loc_key}")
    print(f"    Label: {loc_data.get('label')}")
    print(f"    Lat/Lon: {loc_data.get('lat')}, {loc_data.get('lon')}")

print("\nGroups in cache:")
for group_key in cache.get('groups', {}).keys():
    print(f"  - {group_key}")

print("\nAliases in cache:")
for alias_key, canonical_key in cache.get('aliases', {}).items():
    print(f"  - {alias_key} -> {canonical_key}")

# Check the actual forecast data location
print("\n" + "=" * 70)
print("CHECKING FORECAST DATA LOCATIONS")
print("=" * 70)

for group_key, group_data in cache.get('groups', {}).items():
    if group_key.startswith('loc:'):
        print(f"\nGroup: {group_key}")
        for url_key in list(group_data.keys())[:3]:
            if 'forecast' in url_key.lower():
                print(f"  Forecast URL: {url_key}")
                data = group_data[url_key].get('value', {})
                if 'properties' in data:
                    periods = data['properties'].get('periods', [])
                    if periods:
                        print(f"  First period: {periods[0].get('name')} - {periods[0].get('temperature')} {periods[0].get('temperatureUnit')}")

# Check the issue: Cranberry Township vs Seven Fields
print("\n" + "=" * 70)
print("CHECKING LOCATION NAME MISMATCH")
print("=" * 70)

# The coordinates for 16066 resolve to Cranberry Township
# But the weather.gov points API might return Seven Fields

import requests
headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Test with the coordinates from cache
coords = [
    (40.6941, -80.1201, "From cache alias"),
    (40.6870, -80.0709, "Seven Fields approx"),
]

for lat, lon, desc in coords:
    print(f"\nCoordinates: {lat}, {lon} ({desc})")
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    points_data = requests.get(points_url, headers=headers).json()
    props = points_data['properties']
    
    rel_loc = props.get('relativeLocation', {}).get('properties', {})
    city = rel_loc.get('city')
    state = rel_loc.get('state')
    
    print(f"  NWS City: {city}")
    print(f"  NWS State: {state}")
    print(f"  Grid: {props['gridId']}/{props['gridX']},{props['gridY']}")
    
    # This is what the app uses as location_key
    location_key = f"{city} {state}"
    print(f"  Would create location_key: '{location_key}'")
