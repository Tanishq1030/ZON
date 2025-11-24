#!/usr/bin/env python3
"""
Generate encoded samples from benchmarks/data folder
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

# Input and output directories
DATA_DIR = 'benchmarks/data'
OUTPUT_DIR = 'benchmarks/encoded_samples'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("Encoding benchmarks/data/ files")
print("=" * 80)

# Find all JSON files in data directory
json_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]

for filename in sorted(json_files):
    try:
        filepath = os.path.join(DATA_DIR, filename)
        name = filename.replace('.json', '')
        
        # Load data
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # For sample, limit to 10 records if it's a list
        if isinstance(data, list):
            sample_data = data[:10] if len(data) > 10 else data
            record_count = len(sample_data)
        else:
            sample_data = data
            record_count = 1
        
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
            except:
                pass
        
        # Save files
        with open(f"{OUTPUT_DIR}/{name}.zon", 'w') as f:
            f.write(zon_encoded)
        
        with open(f"{OUTPUT_DIR}/{name}.json", 'w') as f:
            f.write(json_encoded)
        
        if toon_encoded:
            with open(f"{OUTPUT_DIR}/{name}.toon", 'w') as f:
                f.write(toon_encoded)
        
        # Stats
        zon_size = len(zon_encoded)
        json_size = len(json_encoded)
        toon_size = len(toon_encoded) if toon_encoded else None
        reduction = ((json_size - zon_size) / json_size * 100)
        
        status = f"✓ {name:25} | {record_count:3} rec | JSON: {json_size:6} | ZON: {zon_size:6} | {reduction:5.1f}%"
        if toon_size:
            toon_reduction = ((json_size - toon_size) / json_size * 100)
            zon_vs_toon = ((toon_size - zon_size) / toon_size * 100)
            status += f" | TOON: {toon_size:6} ({zon_vs_toon:+5.1f}%)"
        print(status)
        
    except Exception as e:
        print(f"❌ Error with {filename}: {e}")

print("\n" + "=" * 80)
print(f"📁 All samples saved to: {OUTPUT_DIR}/")
print("=" * 80)
