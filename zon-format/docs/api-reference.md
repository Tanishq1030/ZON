# ZON API Reference

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

Complete API documentation for `zon-format` v1.0.4 (Python).

## Installation

```bash
pip install zon-format
```

---

## Encoding Functions

### `encode(data: Any) -> str`

Encodes Python data to ZON format.

**Parameters:**
- `data` (`Any`) - Python data to encode (dicts, lists, primitives)

**Returns:** `str` - ZON-formatted string

**Example:**
```python
import zon

data = {
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False}
    ]
}

encoded = zon.encode(data)
print(encoded)
```

**Output:**
```zon
users:@(2):active,id,name
T,1,Alice
F,2,Bob
```

**Supported Types:**
- ✅ Dicts (nested or flat)
- ✅ Lists (uniform, mixed, primitives)
- ✅ Strings
- ✅ Numbers (integers, floats)
- ✅ Booleans (`T`/`F`)
- ✅ None (`null`)

**Encoding Behavior:**
- **Uniform lists** → Table format (`@(N):columns`)
- **Nested dicts** → Quoted notation (`"{key:value}"`)
- **Primitive lists** → Inline format (`"[a,b,c]"`)
- **Booleans** → `T`/`F` (single character)
- **None** → `null`

---

## Decoding Functions

### `decode(zon_str: str, strict: bool = True) -> Any`

Decodes a ZON format string back to the original Python data structure.

### Parameters

- **`zon_str`** (`str`): The ZON-formatted string to decode
- **`strict`** (`bool`, default: `True`): Enable strict validation

### Strict Mode

**Enabled by default** - Validates table structure during decoding.

**Error Codes:**
- `E001`: Row count mismatch (expected vs actual rows)
- `E002`: Field count mismatch (expected vs actual fields)

**Examples:**

```python
import zon
from zon import ZonDecodeError

# Strict mode (default) - throws on validation errors
zon_data = """
users:@(2):id,name
1,Alice
"""

try:
    data = zon.decode(zon_data)
except ZonDecodeError as e:
    print(e.code)     # "E001"
    print(e.message)  # "[E001] Row count mismatch..."
    print(e.context)  # "Table: users"

# Non-strict mode - allows mismatches
data = zon.decode(zon_data, strict=False)
# Successfully decodes with 1 row instead of declared 2
```

**Output:**
```python
{
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False}
    ]
}
```

**Decoding Guarantees:**
- ✅ **Lossless**: Perfect reconstruction of original data
- ✅ **Type preservation**: Numbers, booleans, None, strings
- ✅ **100% accuracy**: No data loss or corruption

---

## Schema Validation API

ZON provides a runtime schema validation library for LLM guardrails.

### `zon` Builder

Fluent API for defining schemas.

```python
from zon import zon
```

#### Methods

- **`zon.string()`**: Matches any string.
- **`zon.number()`**: Matches any number (no NaN/Infinity).
- **`zon.boolean()`**: Matches `True` or `False`.
- **`zon.enum(values: list)`**: Matches one of the provided string values.
- **`zon.array(schema: ZonSchema)`**: Matches a list where every element matches `schema`.
- **`zon.object(shape: dict)`**: Matches a dict with the specified shape.

#### Modifiers

- **`.optional()`**: Marks a field as optional (can be `None` or missing).
- **`.describe(text: str)`**: Adds a description for prompt generation.

### `validate(input, schema) -> ZonResult`

Validates input against a schema. Accepts either a raw ZON string (which it decodes) or a pre-decoded Python object.

**Returns:** `ZonResult`
```python
class ZonResult:
    success: bool
    data: Any  # Present if success=True
    error: str  # Present if success=False
    issues: list  # List of validation issues
```

**Example:**

```python
from zon import zon, validate

UserSchema = zon.object({
    'name': zon.string(),
    'role': zon.enum(['admin', 'user'])
})

result = validate(llm_output, UserSchema)
if result.success:
    # result.data is the validated data
    print(result.data)
```

---

## Error Handling

### `ZonDecodeError`

Thrown when decoding fails or strict mode validation errors occur.

**Properties:**
- `message` (`str`): Error description
- `code` (`str`, optional): Error code (e.g., "E001", "E002")
- `line` (`int`, optional): Line number where error occurred
- `column` (`int`, optional): Column position
- `context` (`str`, optional): Relevant context snippet

**Example:**

```python
from zon import decode, ZonDecodeError

try:
    data = decode(invalid_zon)
except ZonDecodeError as e:
    print(e.code)      # "E001"
    print(e.line)      # 5
    print(e.context)   # "Table: users"
    print(str(e))      # "[E001] Row count mismatch... (line 5)"
```

### Common Error Codes

| Code | Description | Example |
|------|-------------|----------|
| `E001` | Row count mismatch | Declared `@(3)` but only 2 rows provided |
| `E002` | Field count mismatch | Declared 3 columns but row has 2 values |
| `E301` | Document size exceeds 100MB | Prevents memory exhaustion |
| `E302` | Line length exceeds 1MB | Prevents buffer overflow |
| `E303` | Array length exceeds 1M items | Prevents excessive iteration |
| `E304` | Object key count exceeds 100K | Prevents hash collision |

**Security Limits:**

All security limits (E301-E304) are automatically enforced to prevent DOS attacks. No configuration needed.

**Disable strict mode** to allow row/field count mismatches (E001-E002):

```python
data = zon.decode(zon_string, strict=False)
```

---

## Complete Examples

### Example 1: Simple Object

```python
data = {
    "name": "ZON Format",
    "version": "1.0.4",
    "active": True,
    "score": 98.5
}

encoded = zon.encode(data)
# active:T
# name:ZON Format
# score:98.5
# version:"1.0.4"

decoded = zon.decode(encoded)
# {"name": "ZON Format", "version": "1.0.4", "active": True, "score": 98.5}
```

### Example 2: Uniform Table

```python
data = {
    "employees": [
        {"id": 1, "name": "Alice", "dept": "Eng", "salary": 85000},
        {"id": 2, "name": "Bob", "dept": "Sales", "salary": 72000},
        {"id": 3, "name": "Carol", "dept": "HR", "salary": 65000}
    ]
}

encoded = zon.encode(data)
# employees:@(3):dept,id,name,salary
# Eng,1,Alice,85000
# Sales,2,Bob,72000
# HR,3,Carol,65000

decoded = zon.decode(encoded)
# Identical to original!
```

### Example 3: Mixed Structure

```python
data = {
    "metadata": {"version": "1.0", "env": "prod"},
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ],
    "tags": ["python", "llm", "zon"]
}

encoded = zon.encode(data)
# metadata:"{version:1.0,env:prod}"
# users:@(2):id,name
# 1,Alice
# 2,Bob
# tags:"[python,llm,zon]"

decoded = zon.decode(encoded)
# Identical to original!
```

### Example 4: Nested Objects

```python
data = {
    "config": {
        "database": {
            "host": "localhost",
            "port": 5432,
            "ssl": True
        },
        "cache": {
            "ttl": 3600,
            "enabled": False
        }
    }
}

encoded = zon.encode(data)
# config:"{database:{host:localhost,port:5432,ssl:T},cache:{ttl:3600,enabled:F}}"

decoded = zon.decode(encoded)
# Identical to original!
```

---

## Round-Trip Compatibility

ZON **guarantees lossless round-trips**:

```python
import zon

def test_round_trip(data):
    encoded = zon.encode(data)
    decoded = zon.decode(encoded)
    return data == decoded

# All these pass:
test_round_trip({"name": "test", "value": 123})  # ✅
test_round_trip([1, 2, 3, 4, 5])                  # ✅
test_round_trip([{"id": 1}, {"id": 2}])          # ✅
test_round_trip(None)                             # ✅
test_round_trip("hello")                          # ✅
```

**Verified:**
- ✅ 28/28 unit tests pass
- ✅ 27/27 datasets verified (9 examples + 18 comprehensive)
- ✅ Zero data loss across all test cases

---

## Performance Characteristics

### Encoding Speed
- **Small data (<1KB)**: <1ms
- **Medium data (1-10KB)**: 1-5ms
- **Large data (10-100KB)**: 5-50ms

### Token Efficiency

**Structure**: Mixed uniform tables + nested objects  
**Questions**: 309 total (field retrieval, aggregation, filtering, structure awareness)

#### Efficiency Ranking (Accuracy per 10K Tokens)

Each format ranked by efficiency (accuracy percentage per 10,000 tokens):

```
ZON            ████████████████████ 1430.6 acc%/10K │  99.0% acc │ 692 tokens 👑
CSV            ███████████████████░ 1386.5 acc%/10K │  99.0% acc │ 714 tokens
JSON compact   ████████████████░░░░ 1143.4 acc%/10K │  91.7% acc │ 802 tokens
TOON           ████████████████░░░░ 1132.7 acc%/10K │  99.0% acc │ 874 tokens
JSON           ██████████░░░░░░░░░░  744.6 acc%/10K │  96.8% acc │ 1,300 tokens
```

*Efficiency score = (Accuracy % ÷ Tokens) × 10,000. Higher is better.*

> [!TIP]
> ZON achieves **99.0% accuracy** while using **20.8% fewer tokens** than TOON and **13.7% fewer** than Minified JSON.

#### Per-Model Comparison

Accuracy on the unified dataset with gpt-5-nano:

```
gpt-5-nano (Azure OpenAI)
→ ZON            ████████████████████  99.0% (306/309) │ 692 tokens
  TOON           ████████████████████  99.0% (306/309) │ 874 tokens
  CSV            ████████████████████  99.0% (306/309) │ 714 tokens
  JSON           ███████████████████░  96.8% (299/309) │ 1,300 tokens
  JSON compact   ██████████████████░░  91.7% (283/309) │ 802 tokens
```

**ZON is optimized for:**
- ✅ Uniform lists of objects (tables)
- ✅ Mixed structures (metadata + data)
- ✅ LLM context windows
- ✅ Token-sensitive applications

---

## Choosing ZON

### Use ZON When:
- ✅ Sending data to LLMs
- ✅ Token count matters
- ✅ Data has uniform list structures
- ✅ You need human-readable format
- ✅ Perfect round-trip required

### Consider Alternatives When:
- ❌ Binary formats acceptable (use Protocol Buffers, MessagePack)
- ❌ Primarily deeply nested trees (JSON might be simpler)
- ❌ No LLM usage (stick with JSON)
- ❌ Need streaming/partial decode (not yet supported)

---

## Migration Guide

### From JSON

```python
# Before (JSON)
import json
json_string = json.dumps(data)
parsed = json.loads(json_string)

# After (ZON)
import zon
zon_string = zon.encode(data)
parsed = zon.decode(zon_string)
```

**Benefits:**
- 28-43% fewer tokens
- Same data model
- Lossless conversion

---

## See Also

- [Syntax Cheatsheet](./syntax-cheatsheet.md) - Quick reference
- [Format Specification](./SPEC.md) - Formal grammar
- [LLM Best Practices](./llm-best-practices.md) - Usage guide
- [GitHub Repository](https://github.com/ZON-Format/ZON)
- [PyPI Package](https://pypi.org/project/zon-format/)
