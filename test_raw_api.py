"""
Test raw API data for the same location from different coordinates
"""
import requests
import sys
sys.path.insert(0, r'y:\weather-app')

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

print("=" * 70)
print("TESTING RAW API DATA FOR DIFFERENT COORDINATES")
print("=" * 70)

coords = [
    (40.6870, -80.0709, "Seven Fields"),
    (40.6941, -80.1201, "Cranberry Twp"),
]

for lat, lon, desc in coords:
    print(f"\n{'='*70}")
    print(f"Coordinates: {lat}, {lon} ({desc})")
    print(f"{'='*70}")
    
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    points_data = requests.get(points_url, headers=headers).json()
    props = points_data['properties']
    
    print(f"Grid: {props['gridId']}/{props['gridX']},{props['gridY']}")
    
    forecast_url = props['forecast']
    forecast_data = requests.get(forecast_url, headers=headers).json()
    
    print("\nForecast periods:")
    for p in forecast_data['properties']['periods'][:3]:
        print(f"  {p['name']}: {p['temperature']} {p['temperatureUnit']}")
        
    hourly_url = props['forecastHourly']
    hourly_data = requests.get(hourly_url, headers=headers).json()
    
    print("\nHourly (first 5):")
    for p in hourly_data['properties']['periods'][:5]:
        print(f"  {p['startTime'][-14:-9]}: {p['temperature']} {p['temperatureUnit']}")

print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)
print("""
If the grid points are different (e.g., PBZ/74,77 vs PBZ/72,77),
the forecast data may be slightly different between the two locations.

This is expected behavior - each coordinate maps to a specific grid cell
in the NWS forecast grid system.

However, both grids should return temperatures in Fahrenheit, not Celsius.
""")
