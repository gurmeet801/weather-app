"""
Check the cache for any unit mismatches
"""
import json

with open(r'y:\weather-app\artifacts\weather_cache.json', 'r') as f:
    cache = json.load(f)

print("=" * 70)
print("CHECKING CACHE FOR UNIT MISMATCHES")
print("=" * 70)

# Look at the forecast cache
group = cache.get('groups', {}).get('loc:Seven Fields PA', {})

for key, value in group.items():
    if 'forecast' in key.lower() and 'hourly' not in key.lower():
        print(f"\nForecast cache key: {key}")
        data = value.get('value', {})
        if 'properties' in data:
            periods = data['properties'].get('periods', [])
            print("Periods:")
            for p in periods[:5]:
                temp = p.get('temperature')
                unit = p.get('temperatureUnit')
                print(f"  {p.get('name')}: {temp} {unit}")
                
                # Check if temperature looks suspicious
                if isinstance(temp, (int, float)):
                    if temp > 50:
                        print(f"    WARNING: Temp {temp} seems high for winter in PA!")
                    if -10 < temp < 10:
                        print(f"    NOTE: Temp {temp} in range that could be Celsius or Fahrenheit")

print("\n" + "=" * 70)
print("CHECKING HOURLY CACHE")
print("=" * 70)

for key, value in group.items():
    if 'hourly' in key.lower():
        print(f"\nHourly cache key: {key}")
        data = value.get('value', {})
        if 'properties' in data:
            periods = data['properties'].get('periods', [])
            print("First 5 periods:")
            for p in periods[:5]:
                temp = p.get('temperature')
                unit = p.get('temperatureUnit')
                print(f"  {p.get('startTime')}: {temp} {unit}")
