import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon

def test_type(name, data, expect_success=True):
    print(f"\nTesting {name}...")
    try:
        encoded = zon.encode(data)
        print(f"Encoded: {encoded}")
        decoded = zon.decode(encoded)
        print(f"Decoded: {decoded}")
        
        # For single dict, we expect it to come back as a list containing the dict
        expected = [data] if isinstance(data, dict) else data
        
        # Primitives are now wrapped in {"value": x}
        if data is None:
            expected = [] # None -> []
        elif isinstance(data, (int, float, str, bool)):
            expected = [{"value": data}]
        elif isinstance(data, list):
            # List of primitives?
            new_expected = []
            for item in data:
                if isinstance(item, (dict)): new_expected.append(item)
                else: new_expected.append({"value": item})
            expected = new_expected

        if expect_success:
            if decoded == expected:
                print("PASS")
            else:
                print(f"FAIL: Decoded {decoded} != Expected {expected}")
        else:
            print("UNEXPECTED SUCCESS")
            
    except Exception as e:
        if expect_success:
            traceback.print_exc()
            print("FAIL (Exception)")
        else:
            print(f"PASS (Expected Failure: {e})")

if __name__ == "__main__":
    # 1. Single Dict (Already fixed, verifying)
    test_type("Single Dict", {"a": 1})

    # 2. Primitives (Top level)
    test_type("Integer", 123)
    test_type("String", "hello")
    test_type("Boolean", True)
    test_type("None", None)

    # 3. List of Primitives
    test_type("List of Ints", [1, 2, 3])
    test_type("List of Strings", ["a", "b"])

    # 4. Mixed List (Dicts and Primitives)
    test_type("Mixed List", [{"a": 1}, 2])

    # 5. Nested Structures
    test_type("Nested Dict", {"a": {"b": 1}})
    test_type("List in Dict", {"a": [1, 2]})
