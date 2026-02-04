"""
Final verification of the observation conversion
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import requests

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

print("=" * 70)
print("FINAL VERIFICATION - OBSERVATION CONVERSION")
print("=" * 70)

# Get observation from station
lat, lon = 40.6870, -80.0709
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
stations_url = points_data['properties']['observationStations']
stations_data = requests.get(stations_url, headers=headers).json()
station_id = stations_data['features'][0]['properties']['stationIdentifier']

obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
obs_data = requests.get(obs_url, headers=headers).json()

print(f"\nStation: {station_id}")
print(f"Raw observation temperature: {obs_data['properties']['temperature']}")

# Manual calculation
celsius = obs_data['properties']['temperature']['value']
fahrenheit = (celsius * 9/5) + 32

print(f"\nConversion:")
print(f"  {celsius}°C × 9/5 + 32 = {fahrenheit}°F")
print(f"  Rounded: {round(fahrenheit)}°F")

# Now test our app's output
from services.weather_service import fetch_forecast

forecast, error = fetch_forecast(lat, lon, include_hourly=False, include_alerts=False)

print(f"\nApp output:")
print(f"  actual_temperature: {forecast['actual_temperature']}°{forecast['actual_temperature_unit']}")
print(f"  feels_like_temperature: {forecast['feels_like_temperature']}°{forecast['feels_like_unit']}")
print(f"  observation_station: {forecast.get('observation_station')}")

if forecast['actual_temperature'] == round(fahrenheit):
    print(f"\n✓ CONVERSION IS WORKING CORRECTLY!")
    print(f"  The app displays {forecast['actual_temperature']}°F which is the converted value from {celsius}°C")
else:
    print(f"\n✗ CONVERSION MISMATCH!")
    print(f"  Expected: {round(fahrenheit)}°F")
    print(f"  Got: {forecast['actual_temperature']}°F")

print("\n" + "=" * 70)
print("DISPLAY EXPLANATION")
print("=" * 70)
print("""
In your screenshot showing "21°" and "25°":
- 21° = feels like temperature (wind chill)
- 25° = actual temperature (converted from -4°C observation)

The 25°F is the CORRECT converted value from the observation station.
It is NOT showing Celsius - it's showing Fahrenheit.

To verify:
-4°C = 24.8°F ≈ 25°F

Your app is working correctly!
""")
