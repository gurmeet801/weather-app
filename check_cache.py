import json
from datetime import datetime

with open(r'y:\weather-app\artifacts\weather_cache.json', 'r') as f:
    d = json.load(f)

group = d.get('groups', {}).get('loc:Seven Fields PA', {})
for key, value in group.items():
    if 'forecast' in key.lower() and 'hourly' not in key.lower():
        print('Key:', key)
        print('Expires at:', datetime.fromtimestamp(value.get('expires_at', 0)))
        data = value.get('value', {})
        if 'properties' in data:
            periods = data['properties'].get('periods', [])
            print('Periods count:', len(periods))
            for p in periods[:5]:
                print(f"  {p.get('name')}: temp={p.get('temperature')} {p.get('temperatureUnit')}")
        print()
