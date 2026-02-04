"""
Verify the actual units being returned by weather.gov API
"""
import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from utils import parse_iso_datetime

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

print("=" * 70)
print("CHECKING ACTUAL UNITS FROM WEATHER.GOV API")
print("=" * 70)

# Get points
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
props = points_data['properties']

print(f"\nLocation: {props['relativeLocation']['properties']['city']}, {props['relativeLocation']['properties']['state']}")

# Get forecast (daily)
forecast_url = props['forecast']
forecast_data = requests.get(forecast_url, headers=headers).json()

print(f"\n{'='*70}")
print("RAW FORECAST API RESPONSE - First 5 periods")
print(f"{'='*70}")
for p in forecast_data['properties']['periods'][:5]:
    temp = p['temperature']
    unit = p['temperatureUnit']
    print(f"  {p['name']}:")
    print(f"    temperature: {temp}")
    print(f"    temperatureUnit: '{unit}'")
    print(f"   detailedForecast: {p.get('detailedForecast', 'N/A')[:80]}...")
    
    # If the value were in Celsius, what would it be in Fahrenheit?
    if isinstance(temp, (int, float)):
        c_to_f = (temp * 9/5) + 32
        print(f"    If {temp} were Celsius, it would be {c_to_f:.1f} Fahrenheit")
    print()

# Get hourly
hourly_url = props['forecastHourly']
hourly_data = requests.get(hourly_url, headers=headers).json()

print(f"{'='*70}")
print("RAW HOURLY API RESPONSE - First 5 periods")
print(f"{'='*70}")
for p in hourly_data['properties']['periods'][:5]:
    temp = p['temperature']
    unit = p['temperatureUnit']
    print(f"  {p['startTime']}:")
    print(f"    temperature: {temp}")
    print(f"    temperatureUnit: '{unit}'")
    
    # If the value were in Celsius, what would it be in Fahrenheit?
    if isinstance(temp, (int, float)):
        c_to_f = (temp * 9/5) + 32
        print(f"    If {temp} were Celsius, it would be {c_to_f:.1f} Fahrenheit")
    print()

# Check if there's a unit conversion happening
print(f"{'='*70}")
print("CONVERSION CHECK")
print(f"{'='*70}")
print("Common temperature conversions:")
print("  -5C = 23F")
print("  -3C = 26.6F")  
print("  0C = 32F")
print("  4C = 39.2F")
print("  18C = 64.4F")
print("  21C = 69.8F")
print("  23C = 73.4F")
print()
print("Your observation: Daily shows '23' which matches -5C converted to F")
print("Let me verify what the API actually returns...")
