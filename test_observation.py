"""
Test observation temperature parsing and conversion
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import (
    _parse_observation_temperature,
    _convert_temperature,
    fetch_forecast
)

print("=" * 70)
print("TESTING OBSERVATION TEMPERATURE PARSING")
print("=" * 70)

# Test cases simulating observation API response
test_cases = [
    {"value": 23, "unitCode": "wmoUnit:degC"},  # 23C = 73.4F
    {"value": -5, "unitCode": "wmoUnit:degC"},  # -5C = 23F
    {"value": 4, "unitCode": "wmoUnit:degC"},   # 4C = 39.2F
    {"value": 21, "unitCode": "wmoUnit:degF"},  # Already in F
]

print("\nTest cases:")
for measurement in test_cases:
    temp, unit = _parse_observation_temperature(measurement)
    print(f"  Input: {measurement['value']} with {measurement['unitCode']}")
    print(f"  Parsed: {temp} {unit}")
    
    # Convert to Fahrenheit
    if temp is not None and unit:
        converted = _convert_temperature(temp, unit, "F")
        print(f"  Converted to F: {converted}")
    print()

print("=" * 70)
print("LIVE TEST: Fetch forecast with observation")
print("=" * 70)

lat, lon = 40.6870, -80.0709
forecast, error = fetch_forecast(lat, lon, include_hourly=True, include_alerts=False)

if error:
    print(f"Error: {error}")
else:
    print(f"\nActual temperature: {forecast['actual_temperature']} {forecast['actual_temperature_unit']}")
    print(f"Feels like: {forecast['feels_like_temperature']} {forecast['feels_like_unit']}")
    print(f"Observation station: {forecast.get('observation_station')}")
    print(f"Observation timestamp: {forecast.get('observation_timestamp')}")
    
    # Check if observation is being used
    if forecast.get('observation_station'):
        print("\n  -> Observation data IS being used for current temp")
        print(f"     Station: {forecast['observation_station']}")
    else:
        print("\n  -> No observation data available, using forecast data")
