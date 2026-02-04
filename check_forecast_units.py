"""
Check the forecast API endpoint units
"""
import requests
import json

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

print("=" * 70)
print("CHECKING FORECAST ENDPOINT UNITS")
print("=" * 70)

# Get points
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

# Get forecast
forecast_url = props['forecast']
print(f"\nForecast URL: {forecast_url}")
forecast_data = requests.get(forecast_url, headers=headers).json()

print("\nRAW FORECAST PERIODS:")
for p in forecast_data['properties']['periods'][:7]:
    print(f"  {p['name']}: {p['temperature']} {p['temperatureUnit']}")
    
# Check the hourly
print("\n" + "=" * 70)
print("CHECKING HOURLY ENDPOINT UNITS")
print("=" * 70)

hourly_url = props['forecastHourly']
print(f"\nHourly URL: {hourly_url}")
hourly_data = requests.get(hourly_url, headers=headers).json()

print("\nRAW HOURLY PERIODS (first 10):")
for p in hourly_data['properties']['periods'][:10]:
    print(f"  {p['startTime']}: {p['temperature']} {p['temperatureUnit']}")

# Check if there's any unit mismatch
print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

forecast_temps = [p['temperature'] for p in forecast_data['properties']['periods'][:5]]
hourly_temps = [p['temperature'] for p in hourly_data['properties']['periods'][:24]]

print(f"\nForecast temps (first 5): {forecast_temps}")
print(f"Hourly temps (first 24): min={min(hourly_temps)}, max={max(hourly_temps)}")

# Check for the specific values the user mentioned
print("\n" + "=" * 70)
print("CHECKING USER'S OBSERVATION")
print("=" * 70)
print("User said: 'Daily shows 23 to 18 for tonight'")
print("User said: 'It says -5 and -5C is 23F'")
print()

# The user's screenshot shows:
# - Current temp: 21°
# - Hourly forecast: 14°, 15°, 16°, 16°, 17°, 15°, 11°, 14°
# - Tue 02/03 daily: -3° / 3°

print("Looking at the data:")
print(f"  - Current temp from hourly: {hourly_data['properties']['periods'][0]['temperature']}F")
print(f"  - Tonight's forecast period: {forecast_data['properties']['periods'][0]['temperature']}F")
print(f"  - Tomorrow's high: {forecast_data['properties']['periods'][1]['temperature']}F")

# Check if -5C would be 23F
print(f"\n  - If value were -5C, converted to F: {(-5 * 9/5) + 32:.1f}F")
print(f"  - If value were 23F, that's what API returns for Wednesday high")
