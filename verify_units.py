import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from services.weather_service import fetch_forecast

lat, lon = 40.6870, -80.0709
forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f'Error: {error}')
    sys.exit(1)

print('=== UNITS VERIFICATION ===')
print(f"Current temp: {forecast['actual_temperature']} {forecast['actual_temperature_unit']}")
print(f"Feels like: {forecast['feels_like_temperature']} {forecast['feels_like_unit']}")
print()

print('=== DAILY FORECAST ===')
for day in forecast['daily_forecast'][:5]:
    feels_high = day.get('feels_high')
    feels_low = day.get('feels_low')
    high = day.get('high')
    low = day.get('low')
    unit = day.get('temperatureUnit', 'N/A')
    
    feels_high_str = f"{feels_high}°" if feels_high is not None else "N/A"
    feels_low_str = f"{feels_low}°" if feels_low is not None else "N/A"
    high_str = f"{high}°" if high is not None else "N/A"
    low_str = f"{low}°" if low is not None else "N/A"
    
    print(f"{day['name']}: high={high_str}{unit} (apparent {feels_high_str}), low={low_str}{unit} (apparent {feels_low_str})")

print()
print('=== HOURLY TODAY ===')
for hour in forecast['hourly_today'][:5]:
    temp = hour.get('temperature')
    feels = hour.get('feelsLike')
    unit = hour.get('temperatureUnit', 'N/A')
    
    temp_str = f"{temp}°" if temp is not None else "N/A"
    feels_str = f"{feels}°" if feels is not None else "N/A"
    
    print(f"{hour['time']}: temp={temp_str}{unit} (apparent {feels_str})")
