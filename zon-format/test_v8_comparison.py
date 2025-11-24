#!/usr/bin/env python3
"""
Quick comparison: ZON v8.0 vs v7.0 format on hiking data
"""

import json
import sys
sys.path.insert(0, 'src')

hiking_data = {
    "context": {"task": "Our favorite hikes", "location": "Boulder", "season": "spring_2025"},
    "friends": ["ana", "luis", "sam"],
    "hikes": [
        {"id": 1, "name": "Blue Lake Trail", "distanceKm": 7.5, "elevationGainM": 320, "completedBy": "ana", "wasSunny": True},
        {"id": 2, "name": "Ridge Overlook", "distanceKm": 9.2, "elevationGainM": 540, "completedBy": "luis", "wasSunny": False},
        {"id": 3, "name": "Wildflower Loop", "distanceKm": 5.1, "elevationGainM": 180, "completedBy": "sam", "wasSunny": True}
    ]
}

import zon

# v8.0 Output
encoded_v8 = zon.encode(hiking_data)
json_str = json.dumps(hiking_data, separators=(',', ':'))

print("=" * 80)
print("ZON v8.0 vs v7.0 Format Comparison")
print("=" * 80)

print("\n📊 TOKEN COUNTS:")
print(f"JSON:         {len(json_str)} bytes")
print(f"ZON v8.0:     {len(encoded_v8)} bytes")
print(f"Reduction:    {((len(json_str) - len(encoded_v8)) / len(json_str) * 100):.1f}%")

print("\n📄 ZON v8.0 OUTPUT (ClearText):")
print("-" * 80)
print(encoded_v8)
print("-" * 80)

print("\n✨ VISUAL COMPARISON:")
print("\nv7.0 had:")
print("  #Z:7.0|M=__key__=\"hikes\",context.task=...|S=id:R(1,1)...|A=50")
print("  (Pipes, markers, protocol overhead)")

print("\nv8.0 has:")
print("  context.season: spring_2025")
print("  @hikes(3): id, name, distanceKm, ...")
print("  (Clean YAML + @table syntax)")

# Verify roundtrip
decoded = zon.decode(encoded_v8)
assert decoded == hiking_data
print("\n✅ Roundtrip successful - data perfectly preserved")
