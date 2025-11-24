#!/usr/bin/env python3
"""
Test ZON v7.0 with hiking data to verify:
1. Root Promotion works correctly
2. Boolean values (True/False) are preserved
3. Output is readable (CSV-like)
4. Token reduction vs JSON
"""

import json
import sys
sys.path.insert(0, '/Users/roni/Developer/ZON/zon-format/src')

import zon

# Sample hiking data from the blueprint
hiking_data = {
    "context": {
        "task": "Our favorite hiking trails",
        "location": "Boulder, CO",
        "season": "spring_2025"
    },
    "friends": ["ana", "luis", "sam"],
    "hikes": [
        {
            "id": 1,
            "name": "Blue Lake Trail",
            "distanceKm": 7.5,
            "elevationGainM": 320,
            "completedBy": "ana",
            "wasSunny": True
        },
        {
            "id": 2,
            "name": "Ridge Overlook",
            "distanceKm": 9.2,
            "elevationGainM": 540,
            "completedBy": "luis",
            "wasSunny": False
        },
        {
            "id": 3,
            "name": "Wildflower Loop",
            "distanceKm": 5.1,
            "elevationGainM": 180,
            "completedBy": "sam",
            "wasSunny": True
        }
    ]
}

print("=" * 80)
print("ZON v7.0 - Readable Stream Test")
print("=" * 80)

# Encode
print("\n1. ENCODING...")
encoded = zon.encode(hiking_data)
print("\n--- ZON v7.0 Output ---")
print(encoded)
print()

# Check readability
print("\n2. READABILITY CHECK...")
lines = encoded.split('\n')
print(f"✓ Total lines: {len(lines)}")
print(f"✓ Header starts with #Z:7.0: {lines[0].startswith('#Z:7.0')}")

# Check for nested JSON strings (should NOT exist in v7)
has_nested_json = '"{' in encoded or '}"' in encoded
print(f"✓ No nested JSON strings: {not has_nested_json}")

# Check for T/F tokens
has_boolean_tokens = ',T' in encoded or ',F' in encoded
print(f"✓ Boolean tokens (T/F) present: {has_boolean_tokens}")

# Decode
print("\n3. DECODING...")
decoded = zon.decode(encoded)
print("✓ Decoded successfully")

# Verify structure
print("\n4. STRUCTURE VERIFICATION...")
assert "hikes" in decoded, "Missing 'hikes' key"
assert "context" in decoded, "Missing 'context' key"
assert "friends" in decoded, "Missing 'friends' key"
print("✓ All top-level keys present")

# Verify data integrity
print("\n5. DATA INTEGRITY...")
assert len(decoded["hikes"]) == 3, f"Expected 3 hikes, got {len(decoded['hikes'])}"
print(f"✓ Correct number of hikes: {len(decoded['hikes'])}")

# Verify boolean preservation (CRITICAL TEST)
print("\n6. BOOLEAN PRESERVATION (Critical)...")
for i, hike in enumerate(decoded["hikes"]):
    original = hiking_data["hikes"][i]["wasSunny"]
    restored = hike["wasSunny"]
    print(f"  Hike {i+1}: {hike['name']}")
    print(f"    Original: {original} (type: {type(original).__name__})")
    print(f"    Restored: {restored} (type: {type(restored).__name__})")
    assert original is restored, f"Boolean mismatch at hike {i+1}"
    assert isinstance(restored, bool), f"Type mismatch: expected bool, got {type(restored)}"

print("✓ All booleans preserved correctly with proper types")

# Full equality check
print("\n7. FULL EQUALITY CHECK...")
assert decoded == hiking_data, "Decoded data doesn't match original"
print("✓ Decoded data matches original exactly")

# Token comparison
print("\n8. TOKEN EFFICIENCY...")
json_str = json.dumps(hiking_data, separators=(',', ':'))
json_tokens = len(json_str)
zon_tokens = len(encoded)
reduction = ((json_tokens - zon_tokens) / json_tokens) * 100

print(f"  JSON size: {json_tokens} bytes")
print(f"  ZON size:  {zon_tokens} bytes")
print(f"  Reduction: {reduction:.1f}%")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - ZON v7.0 is working correctly!")
print("=" * 80)
