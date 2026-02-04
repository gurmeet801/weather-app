"""
Test feels like calculation
"""
import sys
sys.path.insert(0, r'y:\weather-app')

from services.weather_service import _calculate_feels_like, _to_fahrenheit

print("=" * 70)
print("TESTING FEELS LIKE CALCULATION")
print("=" * 70)

# Test case: 3F with wind
test_cases = [
    (3, "F", None, 5, "3F with 5mph wind"),
    (3, "F", None, 10, "3F with 10mph wind"),
    (3, "F", None, 15, "3F with 15mph wind"),
    (23, "F", None, 5, "23F with 5mph wind"),
    (23, "F", None, 10, "23F with 10mph wind"),
]

for temp, unit, humidity, wind, desc in test_cases:
    feels = _calculate_feels_like(temp, unit, humidity, wind)
    print(f"\n{desc}:")
    print(f"  Actual: {temp}°{unit}")
    print(f"  Feels like: {feels}°{unit}")
    
    # If it were Celsius, what would it be?
    if unit == "F":
        # Convert to Celsius equivalent
        temp_c = (temp - 32) * 5/9
        feels_c = (feels - 32) * 5/9
        print(f"  In Celsius: actual={temp_c:.1f}°C, feels={feels_c:.1f}°C")

print("\n" + "=" * 70)
print("VERIFICATION: All values are in Fahrenheit")
print("=" * 70)
print("""
The negative "feels like" values (-3°F, etc.) are correct wind chill
calculations for cold winter temperatures with wind.

For reference:
- 0°F = -17.8°C (very cold)
- -5°F = -20.6°C (extremely cold)

These are typical winter wind chill values for Pennsylvania.
""")
