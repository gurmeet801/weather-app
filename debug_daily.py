"""
Debug the daily forecast processing step by step
"""
import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from datetime import datetime
from services.weather_service import build_daily_forecast, _calculate_feels_like
from utils import parse_iso_datetime

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

print("=" * 70)
print("DEBUGGING DAILY FORECAST PROCESSING")
print("=" * 70)

# Get forecast
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
forecast_url = points_data['properties']['forecast']
forecast_data = requests.get(forecast_url, headers=headers).json()
periods = forecast_data['properties']['periods']

print("\nRAW PERIODS FROM API:")
for p in periods[:7]:
    print(f"  {p['name']}: temp={p['temperature']} {p['temperatureUnit']}, isDaytime={p['isDaytime']}")

# Now process with our function
print("\nPROCESSING WITH build_daily_forecast:")
daily = build_daily_forecast(periods)

for day in daily[:5]:
    print(f"\n  {day['name']} ({day['key']}):")
    print(f"    high={day['high']}, low={day['low']}, unit={day['temperatureUnit']}")
    print(f"    feels_high={day['feels_high']}, feels_low={day['feels_low']}")
    print(f"    is_today={day['is_today']}")
    
    # Show what the template would render
    feels_low_str = f"{day['feels_low']}°" if day['feels_low'] is not None else "N/A"
    feels_high_str = f"{day['feels_high']}°" if day['feels_high'] is not None else "N/A"
    actual_low_str = f"{day['low']}°" if day['low'] is not None else "N/A"
    actual_high_str = f"{day['high']}°" if day['high'] is not None else "N/A"
    
    print(f"    TEMPLATE RENDERS: {feels_low_str} / {feels_high_str} (apparent)")
    print(f"    TEMPLATE RENDERS: {actual_low_str} / {actual_high_str} (actual)")

# Now let's manually check what the values would be if they were Celsius
print("\n" + "=" * 70)
print("WHAT IF VALUES WERE CELSIUS?")
print("=" * 70)
for day in daily[:3]:
    if day['low'] is not None and day['high'] is not None:
        low_c = day['low']
        high_c = day['high']
        low_f_from_c = (low_c * 9/5) + 32
        high_f_from_c = (high_c * 9/5) + 32
        print(f"\n  {day['name']}:")
        print(f"    If low={low_c} were Celsius -> {low_f_from_c:.1f}F")
        print(f"    If high={high_c} were Celsius -> {high_f_from_c:.1f}F")

# Check the user's specific observation
print("\n" + "=" * 70)
print("CHECKING USER OBSERVATION:")
print("=" * 70)
print("User said: 'Daily shows 23 to 18 for tonight'")
print("User said: 'It says -5 and -5C is 23F'")
print()
print("Analysis:")
print("  - If API returns 4F for tonight, that's correct for cold PA weather")
print("  - -5C = 23F, but the API says 4F, not 23F")
print("  - The '23' the user sees might be from a different day or feels_like")

# Check Wednesday
wed = next((d for d in daily if 'Wed' in d['name']), None)
if wed:
    print(f"\n  Wednesday data:")
    print(f"    high={wed['high']}F, low={wed['low']}F")
    print(f"    feels_high={wed['feels_high']}, feels_low={wed['feels_low']}")
    if wed['feels_high'] == 18 and wed['high'] == 23:
        print("    -> This matches: feels like 18F, actual high 23F")
    if wed['feels_low'] == -3 and wed['low'] == 3:
        print("    -> This matches: feels like -3F, actual low 3F")
