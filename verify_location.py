import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from datetime import datetime
from services.weather_service import fetch_forecast
from utils import parse_iso_datetime

print("=" * 60)
print("VERIFYING ALL API CALLS USE SAME LOCATION")
print("=" * 60)

# Coordinates for 16066
lat, lon = 40.6870, -80.0709
print(f"\nInput coordinates: lat={lat}, lon={lon}")

# First, call points API directly to see what it returns
headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

print(f"\n=== POINTS API RESPONSE ===")
print(f"Forecast URL: {props['forecast']}")
print(f"Hourly URL: {props['forecastHourly']}")
print(f"Stations URL: {props['observationStations']}")
print(f"Time Zone: {props['timeZone']}")

rel = props.get('relativeLocation', {}).get('properties', {})
print(f"Relative Location: {rel.get('city')}, {rel.get('state')}")

# Now call fetch_forecast to see what it returns
print(f"\n=== FETCH_FORECAST RESULTS ===")
forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=True)

if error:
    print(f"ERROR: {error}")
    sys.exit(1)

print(f"Location: {forecast['location']}")
print(f"Time Zone: {forecast['time_zone']}")

# Check if the forecast period timestamps match the timezone
print(f"\n=== FORECAST PERIODS (first 3) ===")
for period in forecast['period'][:3] if isinstance(forecast['period'], list) else [forecast['period']]:
    if isinstance(period, dict):
        print(f"  {period.get('name')}: startTime={period.get('startTime')}")

print(f"\n=== DAILY FORECAST (first 5 days) ===")
for day in forecast['daily_forecast'][:5]:
    print(f"  {day['name']} ({day['key']}): high={day['high']}°F, low={day['low']}°F")
    print(f"    Apparent: high={day['feels_high']}°F, low={day['feels_low']}°F")
    print(f"    is_today={day['is_today']}")

print(f"\n=== HOURLY TODAY (first 8 hours) ===")
for hour in forecast['hourly_today'][:8]:
    print(f"  {hour['time']}: temp={hour['temperature']}°F (apparent {hour['feelsLike']}°F)")

# Check if "today" is correctly identified
print(f"\n=== 'TODAY' VERIFICATION ===")
now = datetime.now()
print(f"Server local time: {now}")
print(f"Server local date: {now.date()}")

# Check what the API returned as "today"
for day in forecast['daily_forecast'][:3]:
    if day['is_today']:
        print(f"Marked as 'today' in forecast: {day['name']} ({day['key']})")
        
# Verify timestamps in raw API response
print(f"\n=== RAW API TIMESTAMP CHECK ===")
forecast_resp = requests.get(props['forecast'], headers=headers).json()
hourly_resp = requests.get(props['forecastHourly'], headers=headers).json()

print("Forecast periods:")
for p in forecast_resp['properties']['periods'][:3]:
    dt = parse_iso_datetime(p['startTime'])
    print(f"  {p['name']}: {p['startTime']} -> date={dt.date() if dt else 'N/A'}")

print("Hourly periods (first 3):")
for p in hourly_resp['properties']['periods'][:3]:
    dt = parse_iso_datetime(p['startTime'])
    print(f"  Hour {p['startTime']}: date={dt.date() if dt else 'N/A'}")

print(f"\n=== VERIFICATION COMPLETE ===")
