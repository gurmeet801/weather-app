"""
Debug what the template actually renders
"""
from flask import Flask, render_template_string
import requests
import sys
sys.path.insert(0, r'y:\weather-app')
from services.weather_service import build_daily_forecast

headers = {'User-Agent': 'TestScript/1.0 (test@example.com)', 'Accept': 'application/geo+json'}

# Coordinates for 16066 (Seven Fields, PA)
lat, lon = 40.6870, -80.0709

# Get forecast
points_url = f"https://api.weather.gov/points/{lat},{lon}"
points_data = requests.get(points_url, headers=headers).json()
forecast_url = points_data['properties']['forecast']
forecast_data = requests.get(forecast_url, headers=headers).json()
periods = forecast_data['properties']['periods']

daily = build_daily_forecast(periods)

# Simulate template rendering
print("=" * 70)
print("SIMULATING TEMPLATE RENDERING")
print("=" * 70)

template_str = """
{% for day in daily[:5] %}
Day: {{ day.name }}
  Low column:
    feels_low value: {{ day.feels_low }}
    low value: {{ day.low }}
    Renders: {% if day.feels_low is not none %}{{ day.feels_low }}°{% elif day.low is not none %}{{ day.low }}°{% else %}&nbsp;{% endif %}
    Then: {% if day.feels_low is not none and day.low is not none %}{{ day.low }}°{% else %}&nbsp;{% endif %}
  High column:
    feels_high value: {{ day.feels_high }}
    high value: {{ day.high }}
    Renders: {% if day.feels_high is not none %}{{ day.feels_high }}°{% elif day.high is not none %}{{ day.high }}°{% else %}&nbsp;{% endif %}
    Then: {% if day.feels_high is not none and day.high is not none %}{{ day.high }}°{% else %}&nbsp;{% endif %}
{% endfor %}
"""

app = Flask(__name__)
with app.app_context():
    result = render_template_string(template_str, daily=daily)
    print(result)

# Now let's look at the exact structure the template receives
print("\n" + "=" * 70)
print("RAW DAILY FORECAST DATA")
print("=" * 70)
import json
print(json.dumps(daily[:3], indent=2))
