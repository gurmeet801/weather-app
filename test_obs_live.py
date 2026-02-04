"""
Test live observation data
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import requests
from services.weather_service import (
    _parse_observation_temperature,
    _convert_temperature,
    _parse_observation_humidity,
    _parse_observation_wind_mph
)

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

print("=" * 70)
print("TESTING LIVE OBSERVATION DATA")
print("=" * 70)

# Get a station near Seven Fields
lat, lon = 40.6870, -80.0709
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
stations_url = points_data['properties']['observationStations']

stations_data = requests.get(stations_url, headers=headers).json()
station = stations_data['features'][0]
station_id = station['properties']['stationIdentifier']

print(f"\nUsing station: {station_id}")

# Get observation
obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
obs_data = requests.get(obs_url, headers=headers).json()
props = obs_data['properties']

print(f"\nRaw observation data:")
print(f"  Timestamp: {props.get('timestamp')}")
print(f"  Temperature: {props.get('temperature')}")
print(f"  Humidity: {props.get('relativeHumidity')}")
print(f"  Wind Speed: {props.get('windSpeed')}")

# Parse using our functions
temp_val, temp_unit = _parse_observation_temperature(props.get('temperature'))
humidity = _parse_observation_humidity(props.get('relativeHumidity'))
wind = _parse_observation_wind_mph(props.get('windSpeed'))

print(f"\nParsed values:")
print(f"  Temperature: {temp_val} {temp_unit}")
print(f"  Humidity: {humidity}")
print(f"  Wind: {wind} mph")

# Convert to Fahrenheit
if temp_val is not None and temp_unit:
    converted = _convert_temperature(temp_val, temp_unit, "F")
    print(f"\nConverted to Fahrenheit:")
    print(f"  Original: {temp_val} {temp_unit}")
    print(f"  Converted: {converted} F")
    print(f"  Rounded: {int(round(converted))} F")

# Now test full fetch_forecast
print("\n" + "=" * 70)
print("TESTING FULL FETCH_FORECAST")
print("=" * 70)

from services.weather_service import fetch_forecast

forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error: {error}")
else:
    print(f"\nResults from fetch_forecast:")
    print(f"  Actual temp: {forecast['actual_temperature']} {forecast['actual_temperature_unit']}")
    print(f"  Feels like: {forecast['feels_like_temperature']} {forecast['feels_like_unit']}")
    print(f"  Humidity: {forecast['humidity']}")
    print(f"  Observation station: {forecast.get('observation_station')}")
    
    # Check if observation is being used
    if forecast.get('observation_station'):
        print(f"\n  -> Using observation data from: {forecast['observation_station']}")
        print(f"     Observation was converted from Celsius to Fahrenheit")
    else:
        print(f"\n  -> Using forecast data (no observation available)")
