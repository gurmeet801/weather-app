import json
import sys
sys.path.insert(0, r'y:\weather-app')

from datetime import datetime
from utils import parse_iso_datetime

# Load the actual cached forecast data
with open(r'y:\weather-app\artifacts\weather_cache.json', 'r') as f:
    d = json.load(f)

group = d.get('groups', {}).get('loc:Seven Fields PA', {})
forecast_key = None
for key in group.keys():
    if 'forecast' in key.lower() and 'hourly' not in key.lower():
        forecast_key = key
        break

if not forecast_key:
    print("No forecast key found")
    sys.exit(1)

data = group[forecast_key]['value']
periods = data['properties']['periods']

print("=== RAW PERIODS FROM CACHE ===")
for p in periods[:7]:
    print(f"  {p['name']}: temp={p['temperature']} {p['temperatureUnit']}, isDaytime={p['isDaytime']}, start={p['startTime']}")

print("\n=== TRACING build_daily_forecast ===")

grouped = {}
order = []
today = None

for period in periods:
    dt = parse_iso_datetime(period.get("startTime"))
    if not dt:
        print(f"Skipping period with no startTime: {period.get('name')}")
        continue
    if today is None:
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        today = now.date()
        print(f"Today is: {today}")
    if today and dt.date() < today:
        print(f"Skipping period before today: {period.get('name')} on {dt.date()}")
        continue
    
    day_key = dt.date().isoformat()
    if day_key not in grouped:
        grouped[day_key] = {
            "date": dt,
            "key": day_key,
            "high": None,
            "low": None,
            "all_high": None,
            "all_low": None,
            "temperatureUnit": period.get("temperatureUnit"),
        }
        order.append(day_key)
        print(f"New day: {day_key} ({period.get('name')})")
    
    entry = grouped[day_key]
    if today and day_key == today.isoformat():
        print(f"  This is today: {day_key}")
    
    temp = period.get("temperature")
    unit = period.get("temperatureUnit")
    
    print(f"  Processing {period.get('name')}: temp={temp} {unit}, isDaytime={period.get('isDaytime')}")
    
    if isinstance(temp, (int, float)):
        entry["all_high"] = temp if entry["all_high"] is None else max(entry["all_high"], temp)
        entry["all_low"] = temp if entry["all_low"] is None else min(entry["all_low"], temp)
        if period.get("isDaytime"):
            entry["high"] = temp if entry["high"] is None else max(entry["high"], temp)
        else:
            entry["low"] = temp if entry["low"] is None else min(entry["low"], temp)
        print(f"    Updated: all_high={entry['all_high']}, all_low={entry['all_low']}, high={entry['high']}, low={entry['low']}")
    else:
        print(f"    WARNING: temp is not a number: {temp!r} (type: {type(temp)})")

print("\n=== FINAL DAILY FORECAST ===")
for day_key in order[:5]:
    entry = grouped[day_key]
    high = entry.get("high") if entry.get("high") is not None else entry.get("all_high")
    low = entry.get("low") if entry.get("low") is not None else entry.get("all_low")
    print(f"  {day_key}: high={high}, low={low}, unit={entry.get('temperatureUnit')}")
