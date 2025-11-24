import os
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import zon

DATA_DIR = Path(__file__).parent / "data"
SAMPLES_DIR = Path(__file__).parent / "encoded_samples"

def verify_and_inspect():
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return

    SAMPLES_DIR.mkdir(exist_ok=True)
    
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    
    print(f"{'Dataset':<20} | {'Status':<10} | {'Original (B)':<12} | {'ZON (B)':<12} | {'Compression':<12}")
    print("-" * 80)
    
    for filename in files:
        filepath = DATA_DIR / filename
        with open(filepath, 'r') as f:
            original_data = json.load(f)
            
        # 1. Encode
        start_t = time.time()
        encoded_zon = zon.encode(original_data)
        encode_time = (time.time() - start_t) * 1000
        
        # 2. Decode
        start_t = time.time()
        decoded_data = zon.decode(encoded_zon)
        decode_time = (time.time() - start_t) * 1000
        
        # 3. Verify
        # Convert both to JSON strings to compare (handles tuple/list differences if any, though ZON uses lists)
        # But direct comparison is better for types
        is_match = original_data == decoded_data
        
        status = "✅ PASS" if is_match else "❌ FAIL"
        
        # 4. Stats
        orig_size = len(json.dumps(original_data, separators=(',', ':')))
        zon_size = len(encoded_zon)
        compression = (1 - zon_size / orig_size) * 100
        
        print(f"{filename:<20} | {status:<10} | {orig_size:<12} | {zon_size:<12} | {compression:>10.1f}%")
        
        if not is_match:
            print(f"  FAILED: {filename}")
            # Save debug files
            with open(SAMPLES_DIR / f"{filename}.debug.orig.json", 'w') as f:
                json.dump(original_data, f, indent=2)
            with open(SAMPLES_DIR / f"{filename}.debug.decoded.json", 'w') as f:
                json.dump(decoded_data, f, indent=2)
            print(f"  Saved debug files to {SAMPLES_DIR}")

        # Save sample for inspection
        zon_path = SAMPLES_DIR / f"{filename.replace('.json', '.zon')}"
        with open(zon_path, 'w') as f:
            f.write(encoded_zon)

    print("-" * 80)
    print(f"Samples saved to {SAMPLES_DIR}")
    
    # Inspect orders.zon specifically as it was the focus
    orders_zon = SAMPLES_DIR / "orders.zon"
    if orders_zon.exists():
        print("\n--- Inspection: orders.zon (First 10 lines) ---")
        with open(orders_zon, 'r') as f:
            print("".join(f.readlines()[:10]))

if __name__ == "__main__":
    verify_and_inspect()
