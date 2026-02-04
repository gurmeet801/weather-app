"""
Final verification: Compare raw API data vs processed data for the exact location.
This will show if there's any inconsistency between endpoints.
"""
import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from datetime import datetime
from utils import parse_iso_datetime

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

print("=" * 70)
print("COMPARING RAW API DATA vs PROCESSED DATA")
print("=" * 70)

# Get points
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

print(f"\nLocation: {props['relativeLocation']['properties']['city']}, {props['relativeLocation']['properties']['state']}")
print(f"Grid: {props['gridId']}/{props['gridX']},{props['gridY']}")
print(f"Timezone: {props['timeZone']}")

# Get forecast (daily)
forecast_url = props['forecast']
forecast_data = requests.get(forecast_url, headers=headers).json()

# Get hourly
hourly_url = props['forecastHourly']
hourly_data = requests.get(hourly_url, headers=headers).json()

print(f"\n{'='*70}")
print("RAW API: FORECAST (Daily) - First 7 periods")
print(f"{'='*70}")
for p in forecast_data['properties']['periods'][:7]:
    print(f"  {p['name']}: temp={p['temperature']} deg {p['temperatureUnit']}, isDaytime={p['isDaytime']}")

print(f"\n{'='*70}")
print("RAW API: HOURLY - First 24 hours")
print(f"{'='*70}")
hourly_periods = hourly_data['properties']['periods'][:24]
for p in hourly_periods:
    print(f"  {p['startTime']}: temp={p['temperature']} deg {p['temperatureUnit']}")

# Now group hourly by date to see if there's a mismatch
print(f"\n{'='*70}")
print("HOURLY GROUPED BY DATE (first 24 hours)")
print(f"{'='*70}")
grouped = {}
for p in hourly_periods:
    dt = parse_iso_datetime(p['startTime'])
    date_key = dt.date().isoformat()
    if date_key not in grouped:
        grouped[date_key] = {'temps': [], 'hours': 0}
    grouped[date_key]['temps'].append(p['temperature'])
    grouped[date_key]['hours'] += 1

for date_key, data in sorted(grouped.items()):
    temps = data['temps']
    print(f"  {date_key} ({data['hours']} hours): min={min(temps)} deg F, max={max(temps)} deg F")

print(f"\n{'='*70}")
print("COMPARISON: Daily Forecast vs Hourly Aggregated")
print(f"{'='*70}")

# Get daily from our processed data
from services.weather_service import build_daily_forecast
daily = build_daily_forecast(forecast_data['properties']['periods'])

for day in daily[:5]:
    date_key = day['key']
    if date_key in grouped:
        hourly_min = min(grouped[date_key]['temps'])
        hourly_max = max(grouped[date_key]['temps'])
        daily_low = day['low']
        daily_high = day['high']
        
        low_ok = daily_low == hourly_min
        high_ok = daily_high == hourly_max
        
        low_status = "OK" if low_ok else f"MISMATCH (hourly={hourly_min})"
        high_status = "OK" if high_ok else f"MISMATCH (hourly={hourly_max})"
        
        print(f"  {day['name']} ({date_key}):")
        print(f"    Daily API:  low={daily_low} deg F [{low_status}], high={daily_high} deg F [{high_status}]")
        print(f"    Hourly API: range={hourly_min} deg F to {hourly_max} deg F")
    else:
        print(f"  {day['name']} ({date_key}): No hourly data available")

print(f"\n{'='*70}")
print("VERIFICATION COMPLETE")
print(f"{'='*70}")
