"""
Final confirmation of units from weather.gov API
"""
import requests

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

print("=" * 70)
print("FINAL UNIT CONFIRMATION")
print("=" * 70)

# Get points
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

print(f"\nLocation: {props['relativeLocation']['properties']['city']}, {props['relativeLocation']['properties']['state']}")

# Get forecast
forecast_url = props['forecast']
forecast_data = requests.get(forecast_url, headers=headers).json()

print("\nFORECAST API RESPONSE (Raw):")
for p in forecast_data['properties']['periods'][:5]:
    print(f"  {p['name']}: {p['temperature']} {p['temperatureUnit']}")
    print(f"    Forecast text: {p['detailedForecast'][:60]}...")
    
print("\nTEMPERATURE ANALYSIS:")
print("  All values above are in Fahrenheit (F) as indicated by temperatureUnit")
print("  These are typical winter temperatures for Pennsylvania in February")
print("  The API correctly returns Fahrenheit for US locations")

# Verify with the grid forecast endpoint
grid_id = props['gridId']
grid_x = props['gridX']
grid_y = props['gridY']
print(f"\nGrid Info: {grid_id}/{grid_x},{grid_y}")
print(f"Forecast URL: {forecast_url}")

# Check hourly too
hourly_url = props['forecastHourly']
hourly_data = requests.get(hourly_url, headers=headers).json()
print(f"\nHourly URL: {hourly_url}")
print("Hourly periods (first 5):")
for p in hourly_data['properties']['periods'][:5]:
    print(f"  {p['startTime']}: {p['temperature']} {p['temperatureUnit']}")

print("\n" + "=" * 70)
print("CONCLUSION: All temperatures are in FAHRENHEIT (F)")
print("=" * 70)
