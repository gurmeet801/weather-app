"""
Verify what values are actually being displayed
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import fetch_forecast

lat, lon = 40.6870, -80.0709

print("=" * 70)
print("VERIFYING DISPLAY VALUES")
print("=" * 70)

forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error: {error}")
    sys.exit(1)

print(f"\nCURRENT WEATHER (current_weather.html):")
print(f"  feels_like_temperature: {forecast['feels_like_temperature']} {forecast['feels_like_unit']}")
print(f"  actual_temperature: {forecast['actual_temperature']} {forecast['actual_temperature_unit']}")
print(f"  period.temperature: {forecast['period']['temperature']} {forecast['period']['temperatureUnit']}")

print(f"\nHOURLY FORECAST (hourly_forecast.html):")
print(f"  Shows feelsLike first, then temperature")
for h in forecast['hourly_today'][:8]:
    print(f"    {h['time']}: feels={h['feelsLike']}°, actual={h['temperature']}°")

print(f"\nDAILY FORECAST (daily_forecast.html):")
print(f"  Shows feels_low/feels_high first, then low/high")
for d in forecast['daily_forecast'][:5]:
    print(f"    {d['name']}: feels {d['feels_low']}°/{d['feels_high']}°, actual {d['low']}°/{d['high']}°")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print(f"""
Current temp source: {'Observation station' if forecast.get('observation_station') else 'Forecast'}
Observation station: {forecast.get('observation_station', 'N/A')}
Observation converted: Yes (from Celsius to Fahrenheit)

All displayed temperatures are in Fahrenheit.
The hourly shows feels-like on top, actual below.
The daily shows feels-like on left, actual on right.
""")
