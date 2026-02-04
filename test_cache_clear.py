"""
Test cache clearing functionality
"""
import sys
sys.path.insert(0, r'y:\weather-app')

import os
import json
from utils import (
    clear_cache,
    clear_location_cache,
    delete_location_cache,
    location_group_key,
    _load_cache_file,
    CACHE_FILE
)

print("=" * 70)
print("TESTING CACHE CLEARING")
print("=" * 70)

# First, check if cache file exists
print(f"\nCache file path: {CACHE_FILE}")
print(f"Cache file exists: {os.path.exists(CACHE_FILE)}")

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    print(f"\nCache keys: {list(cache.keys())}")
    print(f"Locations: {list(cache.get('locations', {}).keys())}")
    print(f"Groups: {list(cache.get('groups', {}).keys())}")
    print(f"Aliases: {list(cache.get('aliases', {}).keys())}")
    
    # Check the specific location group
    location_key = "Seven Fields PA"
    group_key = location_group_key(location_key)
    print(f"\nLocation group key for '{location_key}': {group_key}")
    
    if group_key in cache.get('groups', {}):
        print(f"Group exists with {len(cache['groups'][group_key])} entries")
        for key in list(cache['groups'][group_key].keys())[:3]:
            print(f"  - {key}")
    else:
        print("Group NOT found in cache!")
        print(f"Available groups: {list(cache.get('groups', {}).keys())}")
    
    # Test clear_location_cache
    print("\n" + "=" * 70)
    print("TESTING clear_location_cache")
    print("=" * 70)
    
    print(f"\nClearing cache for location: {location_key}")
    clear_location_cache(location_key)
    
    # Reload and check
    cache_after = _load_cache_file()
    if group_key in cache_after.get('groups', {}):
        print(f"ERROR: Group {group_key} still exists after clearing!")
    else:
        print(f"SUCCESS: Group {group_key} was removed")
    
    # Test clear_cache (full clear)
    print("\n" + "=" * 70)
    print("TESTING clear_cache (full)")
    print("=" * 70)
    
    print(f"\nCache file exists before clear: {os.path.exists(CACHE_FILE)}")
    clear_cache()
    print(f"Cache file exists after clear: {os.path.exists(CACHE_FILE)}")
    
    if os.path.exists(CACHE_FILE):
        print("ERROR: Cache file still exists after clear_cache()!")
        # Check if it was recreated
        cache_new = _load_cache_file()
        print(f"New cache keys: {list(cache_new.keys())}")
        print(f"New groups: {list(cache_new.get('groups', {}).keys())}")
else:
    print("No cache file found to test")
