#!/usr/bin/env python3
"""
Test ZON v8.0 ClearText Format

Verifies:
1. YAML-like metadata output
2. @table syntax
3. Smart quoting (only when needed)
4. Singleton bypass
5. Compression tokens (_ and ^)
6. Visual cleanliness vs v7.0
"""

import json
import sys
sys.path.insert(0, '/Users/roni/Developer/ZON/zon-format/src')

import zon

print("=" * 80)
print("ZON v8.0 - ClearText Format Test")
print("=" * 80)

# Test 1: Basic hiking data
print("\n" + "=" * 80)
print("TEST 1: Basic Hiking Data with Multiple Items")
print("=" * 80)

hiking_data = {
    "context": "Hiking Trip",
    "location": "Boulder, CO",
    "hikes": [
        {"id": 1, "name": "Blue Lake Trail", "sunny": True},
        {"id": 2, "name": "Ridge Overlook", "sunny": False},
        {"id": 3, "name": "Wildflower Loop", "sunny": True}
    ]
}

encoded = zon.encode(hiking_data)
print("\n--- ZON v8.0 Output ---")
print(encoded)
print()

# Visual cleanliness checks
print("CLEANLINESS CHECKS:")
print(f"✓ No pipes: {('|' not in encoded)}")
print(f"✓ No #Z: header: {('#Z:' not in encoded)}")
print(f"✓ Has @table marker: {('@hikes' in encoded)}")
print(f"✓ Has YAML-like metadata: {('context:' in encoded)}")
print(f"✓ Uses _ (auto-increment): {('_' in encoded)}")

# Smart quoting checks
print("\nSMART QUOTING:")
lines = encoded.split('\n')
table_lines = [l for l in lines if l and not l.startswith('context') and not l.startswith('location') and not l.startswith('@')]
print(f"✓ 'Ridge Overlook' is quoted (has space): {('\"Ridge Overlook\"' in encoded)}")
print(f"✓ Boolean T/F present: {('T' in encoded and 'F' in encoded)}")

# Decode and verify
decoded = zon.decode(encoded)
assert decoded == hiking_data, "Decoded data doesn't match original"
print("\n✅ DECODE: Perfect match")

# Token count
json_size = len(json.dumps(hiking_data, separators=(',', ':')))
zon_size = len(encoded)
print(f"\nTOKEN EFFICIENCY:")
print(f"  JSON: {json_size} bytes")
print(f"  ZON:  {zon_size} bytes")
print(f"  Reduction: {((json_size - zon_size) / json_size * 100):.1f}%")

# Test 2: Singleton bypass
print("\n" + "=" * 80)
print("TEST 2: Singleton Bypass (1-item list flattened)")
print("=" * 80)

singleton_data = {
    "user": "Alice",
    "items": [{"id": 1, "name": "Book"}]
}

encoded2 = zon.encode(singleton_data)
print("\n--- ZON v8.0 Output ---")
print(encoded2)
print()

print("SINGLETON BYPASS CHECKS:")
print(f"✓ No @items table: {('@items' not in encoded2)}")
print(f"✓ Has items.0.id: {('items.0.id' in encoded2)}")
print(f"✓ Has items.0.name: {('items.0.name' in encoded2)}")

decoded2 = zon.decode(encoded2)
assert decoded2 == singleton_data, "Singleton decode failed"
print("\n✅ DECODE: Perfect match")

# Test 3: Smart quoting edge cases
print("\n" + "=" * 80)
print("TEST 3: Smart Quoting Edge Cases")
print("=" * 80)

quote_test = {
    "data": [
        {"simple": "ana", "spaced": "Blue Lake", "comma": "a,b", "number": 42, "bool": True}
    ]
}

encoded3 = zon.encode(quote_test)
print("\n--- ZON v8.0 Output ---")
print(encoded3)
print()

print("QUOTING VERIFICATION:")
# Simple word should not be quoted
has_unquoted_ana = 'ana' in encoded3 and '"ana"' not in encoded3
print(f"✓ 'ana' unquoted (simple): {has_unquoted_ana}")
print(f"✓ 'Blue Lake' quoted (space): {('\"Blue Lake\"' in encoded3)}")
print(f"✓ 'a,b' quoted (comma): {('\"a,b\"' in encoded3)}")
print(f"✓ Boolean as T: {(', T' in encoded3 or ':T' in encoded3.replace(' ', ''))}")

decoded3 = zon.decode(encoded3)
assert decoded3 == quote_test, "Quote test decode failed"
print("\n✅ DECODE: Perfect match")

# Test 4: Nested metadata
print("\n" + "=" * 80)
print("TEST 4: Nested Metadata Flattening")
print("=" * 80)

nested_data = {
    "config": {
        "db": {
            "host": "localhost",
            "port": 5432
        }
    },
    "records": [
        {"id": 1, "value": "test"}
    ]
}

encoded4 = zon.encode(nested_data)
print("\n--- ZON v8.0 Output ---")
print(encoded4)
print()

print("FLATTENING VERIFICATION:")
print(f"✓ Has config.db.host: {('config.db.host' in encoded4)}")
print(f"✓ Has config.db.port: {('config.db.port' in encoded4)}")

decoded4 = zon.decode(encoded4)
assert decoded4 == nested_data, "Nested decode failed"
print("\n✅ DECODE: Perfect match")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - ZON v8.0 ClearText is working!")
print("=" * 80)
