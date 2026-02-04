"""
Test geocoding for 16066
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.geocode_service import geocode_address

print("=" * 70)
print("TESTING GEOCODE FOR 16066")
print("=" * 70)

lat, lon, city, state, display_name, error = geocode_address("16066")

if error:
    print(f"Error: {error}")
else:
    print(f"Lat: {lat}")
    print(f"Lon: {lon}")
    print(f"City: {city}")
    print(f"State: {state}")
    print(f"Display: {display_name}")
    
    # Convert to float
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        print(f"\nCoordinates: {lat_f}, {lon_f}")
        
        # Check what grid this would map to
        import requests
        headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}
        points_url = f"https://api.weather.gov/points/{lat_f},{lon_f}"
        points_data = requests.get(points_url, headers=headers).json()
        
        props = points_data['properties']
        print(f"Grid: {props['gridId']}/{props['gridX']},{props['gridY']}")
        print(f"Forecast URL: {props['forecast']}")
        
        # Get forecast
        forecast_data = requests.get(props['forecast'], headers=headers).json()
        print("\nForecast periods:")
        for p in forecast_data['properties']['periods'][:3]:
            print(f"  {p['name']}: {p['temperature']} {p['temperatureUnit']}")
            
    except Exception as e:
        print(f"Error: {e}")
