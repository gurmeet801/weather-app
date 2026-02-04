"""
Test specifically for ZIP 16066
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.geocode_service import geocode_address
from services.weather_service import fetch_forecast

print("=" * 70)
print("TESTING ZIP 16066 SPECIFICALLY")
print("=" * 70)

# Geocode 16066
lat, lon, city, state, display_name, error = geocode_address("16066")

if error:
    print(f"Geocode error: {error}")
else:
    print(f"\nGeocoded 16066 to:")
    print(f"  Lat: {lat}")
    print(f"  Lon: {lon}")
    print(f"  City: {city}")
    print(f"  State: {state}")
    print(f"  Display: {display_name}")
    
    # Fetch forecast for these coordinates
    print(f"\nFetching forecast...")
    forecast, error = fetch_forecast(
        lat, lon,
        preferred_city=city,
        preferred_state=state,
        include_hourly=True,
        include_alerts=False
    )
    
    if error:
        print(f"Forecast error: {error}")
    else:
        print(f"\nForecast results:")
        print(f"  Location: {forecast['location']}")
        print(f"  Location key: {forecast['location_key']}")
        print(f"  Actual temp: {forecast['actual_temperature']} {forecast['actual_temperature_unit']}")
        print(f"  Feels like: {forecast['feels_like_temperature']} {forecast['feels_like_unit']}")
        print(f"  Observation station: {forecast.get('observation_station')}")
        
        print(f"\n  Period (forecast):")
        print(f"    Name: {forecast['period']['name']}")
        print(f"    Temp: {forecast['period']['temperature']} {forecast['period']['temperatureUnit']}")
        
        if forecast.get('next_period'):
            print(f"\n  Next period:")
            print(f"    Name: {forecast['next_period']['name']}")
            print(f"    Temp: {forecast['next_period']['temperature']} {forecast['next_period']['temperatureUnit']}")
        
        print(f"\n  Hourly today (first 5):")
        for h in forecast['hourly_today'][:5]:
            print(f"    {h['time']}: {h['temperature']}° (feels {h['feelsLike']}°)")
        
        print(f"\n  Daily forecast (first 5):")
        for d in forecast['daily_forecast'][:5]:
            print(f"    {d['name']}: high={d['high']}° low={d['low']}° (feels {d['feels_high']}°/{d['feels_low']}°)")

# Compare with direct coordinates
print("\n" + "=" * 70)
print("COMPARING WITH DIRECT COORDINATES")
print("=" * 70)

# These are approximate coordinates for Seven Fields
direct_coords = (40.6870, -80.0709)
print(f"\nDirect coordinates: {direct_coords}")

forecast2, error2 = fetch_forecast(
    direct_coords[0], direct_coords[1],
    include_hourly=False,
    include_alerts=False
)

if not error2:
    print(f"  Location: {forecast2['location']}")
    print(f"  Location key: {forecast2['location_key']}")
    print(f"  Actual temp: {forecast2['actual_temperature']} {forecast2['actual_temperature_unit']}")
