import json
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import fetch_forecast

# Test for 16066 (Seven Fields PA)
lat, lon = 40.6870, -80.0709

forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error: {error}")
    sys.exit(1)

print("=== DAILY FORECAST ===")
for day in forecast['daily_forecast'][:5]:
    print(f"  {day['name']}: high={day['high']}, low={day['low']}, unit={day['temperatureUnit']}")

print("\n=== DAILY DETAILS (from API) ===")
for day in forecast['daily_details'][:3]:
    print(f"  {day['key']}: hours count={len(day['hours'])}")
    if day['hours']:
        first_hour = day['hours'][0]
        print(f"    First hour: {first_hour['time']} - temp={first_hour['temperature']} {first_hour['temperatureUnit']}")

print("\n=== HOURLY TODAY ===")
for hour in forecast['hourly_today'][:5]:
    print(f"  {hour['time']}: temp={hour['temperature']} {hour['temperatureUnit']}")
