"""
Populate the cache by fetching forecast
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import fetch_forecast

print("Populating cache...")
lat, lon = 40.6870, -80.0709
forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error: {error}")
else:
    print(f"Success! Location: {forecast['location']}")
    print(f"Location key: {forecast['location_key']}")
