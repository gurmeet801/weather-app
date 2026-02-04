import requests
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import build_daily_forecast, build_hourly_today

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Get points data for 16066 area
lat, lon = 40.6870, -80.0709
points_url = f'https://api.weather.gov/points/{lat},{lon}'
points_resp = requests.get(points_url, headers=headers)
points_data = points_resp.json()
props = points_data['properties']

# Get forecast (daily)
forecast_url = props['forecast']
forecast_resp = requests.get(forecast_url, headers=headers)
forecast_data = forecast_resp.json()
periods = forecast_data['properties']['periods']

# Get hourly forecast
hourly_url = props['forecastHourly']
hourly_resp = requests.get(hourly_url, headers=headers)
hourly_data = hourly_resp.json()
hourly_periods = hourly_data['properties']['periods']

print('=== RAW API: First 5 forecast periods ===')
for p in periods[:5]:
    print(f"  {p['name']}: temp={p['temperature']} {p['temperatureUnit']}, isDaytime={p['isDaytime']}")

print('\n=== PROCESSED: build_daily_forecast ===')
daily = build_daily_forecast(periods)
for day in daily[:5]:
    print(f"  {day['name']}: high={day['high']}, low={day['low']}, unit={day['temperatureUnit']}")

print('\n=== PROCESSED: build_hourly_today (first 8 hours) ===')
hourly = build_hourly_today(hourly_periods)
for h in hourly[:8]:
    print(f"  {h['time']}: temp={h['temperature']} {h['temperatureUnit']}")
