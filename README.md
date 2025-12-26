# Weather App (Flask + Tailwind)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:8080 in your browser.

## Deploy

- Railway runs the app via `Procfile` using Gunicorn and expects `$PORT`.

## Notes

- Search by address or use your current location; the app geocodes addresses with
  OpenStreetMap Nominatim and fetches forecasts from api.weather.gov.
- Weather.gov and Nominatim require a User-Agent header; set one with:

```bash
export WEATHER_GOV_USER_AGENT="weather-app (you@example.com)"
```
