#!/usr/bin/env python3
"""
Generate encoded samples for visual inspection
"""

import json
import sys
import os
sys.path.insert(0, 'src')

import zon

# Try to import TOON
try:
    import toon_python as toon
    HAS_TOON = True
except ImportError:
    try:
        import toon_format as toon
        HAS_TOON = True
    except ImportError:
        HAS_TOON = False
        print("⚠️  TOON library not found - will skip TOON samples")

# Output directory
OUTPUT_DIR = 'benchmarks/encoded_samples'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Datasets to encode
datasets = [
    ('/tmp/test_random_users.json', 'random_users', 'results'),
    ('/tmp/test_stackoverflow.json', 'stackoverflow', 'items'),
    ('/tmp/test_posts.json', 'posts', None),
    ('/tmp/test_comments.json', 'comments', None),
    ('/tmp/test_users.json', 'users', None),
    ('/tmp/test_github_repos.json', 'github_repos', None),
]

print("=" * 80)
print("Generating Encoded Samples (JSON, ZON, TOON)")
print("=" * 80)

for filepath, name, extract_key in datasets:
    try:
        # Load data
        with open(filepath, 'r') as f:
            raw = json.load(f)
        
        data = raw[extract_key] if extract_key else raw
        if not isinstance(data, list):
            print(f"⚠️  Skipping {name}: Not a list")
            continue
        
        # Limit to first 10 records for readability
        sample_data = data[:10] if len(data) > 10 else data
        
        # Encode in all formats
        zon_encoded = zon.encode(sample_data)
        json_encoded = json.dumps(sample_data, indent=2)
        
        toon_encoded = None
        if HAS_TOON:
            try:
                if hasattr(toon, 'encode'):
                    toon_bytes = toon.encode(sample_data)
                elif hasattr(toon, 'dumps'):
                    toon_bytes = toon.dumps(sample_data)
                toon_encoded = toon_bytes.decode('utf-8') if isinstance(toon_bytes, bytes) else str(toon_bytes)
            except Exception as e:
                print(f"  ⚠️  TOON encoding failed: {e}")
        
        # Save files
        zon_file = f"{OUTPUT_DIR}/{name}.zon"
        json_file = f"{OUTPUT_DIR}/{name}.json"
        toon_file = f"{OUTPUT_DIR}/{name}.toon"
        
        with open(zon_file, 'w') as f:
            f.write(zon_encoded)
        
        with open(json_file, 'w') as f:
            f.write(json_encoded)
        
        if toon_encoded:
            with open(toon_file, 'w') as f:
                f.write(toon_encoded)
        
        # Stats
        zon_size = len(zon_encoded)
        json_size = len(json_encoded)
        toon_size = len(toon_encoded) if toon_encoded else None
        reduction = ((json_size - zon_size) / json_size * 100)
        
        status = f"✓ {name:20} | {len(sample_data):3} records | JSON: {json_size:6} | ZON: {zon_size:6} | {reduction:5.1f}%"
        if toon_size:
            status += f" | TOON: {toon_size:6}"
        print(status)
        
    except FileNotFoundError:
        print(f"⚠️  Skipping {name}: File not found")
    except Exception as e:
        print(f"❌ Error with {name}: {e}")

print("\n" + "=" * 80)
print(f"📁 Encoded samples saved to: {OUTPUT_DIR}/")
print("=" * 80)
print("\nFiles created:")
for filepath, name, _ in datasets:
    zon_path = f"{OUTPUT_DIR}/{name}.zon"
    json_path = f"{OUTPUT_DIR}/{name}.json"
    toon_path = f"{OUTPUT_DIR}/{name}.toon"
    if os.path.exists(zon_path):
        print(f"  • {name}.zon")
        print(f"  • {name}.json")
        if os.path.exists(toon_path):
            print(f"  • {name}.toon")
