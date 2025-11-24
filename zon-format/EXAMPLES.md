# ZON Format Examples

This document provides detailed examples of ZON v8.0 encoding across different data types and structures.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Format Comparison](#format-comparison)
- [Symbol Reference](#symbol-reference)
- [Advanced Examples](#advanced-examples)

## Basic Examples

### Simple List

**JSON**:
```json
[
  {"id": 1, "name": "Alice"},
  {"id": 2, "name": "Bob"}
]
```

**ZON**:
```
@data(2):id,name
1,Alice
_,Bob
```

- `@data(2)` → table with 2 rows
- `_` → auto-increment (2 = 1 + 1)

---

### Nested Object

**JSON**:
```json
{
  "config": {
    "host": "localhost",
    "port": 5432
  },
  "users": [
    {"id": 1, "name": "test"}
  ]
}
```

**ZON**:
```
config.host:localhost
config.port:5432

@users(1):id,name
1,test
```

- Dot notation flattens nesting
- Metadata separated from table with blank line

---

### Arrays in Metadata

**JSON**:
```json
{
  "tags": ["python", "data", "format"],
  "version": "1.0"
}
```

**ZON**:
```
tags:[python,data,format]
version:1.0
```

- No quotes in arrays unless needed
- Compact `[item,item,item]` syntax

---

## Format Comparison

### Example: User Records

**JSON (201 bytes)**:
```json
[
  {"id":1,"name":"Alice","age":30,"active":true,"city":"NYC"},
  {"id":2,"name":"Bob","age":25,"active":false,"city":"LA"},
  {"id":3,"name":"Charlie","age":35,"active":true,"city":"NYC"}
]
```

**TOON (formatted, ~180 bytes)**:
```
users[3]{id,name,age,active,city}
1,Alice,30,true,"NYC"
2,Bob,25,false,"LA"
3,Charlie,35,true,"NYC"
```

**ZON (106 bytes - 47% smaller than JSON)**:
```
@data(3):active,age,city,id,name
T,30,NYC,1,Alice
F,25,LA,_,Bob
T,35,^,_,Charlie
```

**Why ZON wins**:
- ✅ No quotes on simple strings
- ✅ `T`/`F` instead of `true`/`false` (3 bytes saved per boolean)
- ✅ `_` for auto-increment IDs
- ✅ `^` for repeated values (NYC)
- ✅ No spaces after delimiters

---

## Symbol Reference

### Metadata Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `:` | Key-value separator | `name:Alice` |
| `.` | Nested object delimiter | `user.name:Alice` |
| `[]` | Array | `tags:[a,b,c]` |
| `,` | Array/table delimiter | No quotes around spaces |

### Table Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `@` | Table marker | `@users(10):id,name` |
| `()` | Row count | `@data(5)` |
| `:` | Header separator | `@table:col1,col2` |

### Compression Tokens

| Token | Meaning | Example | Output |
|-------|---------|---------|--------|
| `_` | Auto-increment | `1,_,_` | `1,2,3` |
| `^` | Repeat previous | `red,^,blue` | `red,red,blue` |
| `T` | Boolean true | `T` | `true` |
| `F` | Boolean false | `F` | `false` |
| `null` | Null value | `null` | `null` |

---

## Advanced Examples

### Complex Nested Data

**Input**:
```json
{
  "company": "Acme Inc",
  "employees": [
    {
      "id": 1,
      "name": "John Doe",
      "department": "Engineering",
      "skills": ["Python", "Go"],
      "active": true
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "department": "Engineering",
      "skills": ["Java", "Kotlin"],
      "active": true
    }
  ]
}
```

**ZON Output**:
```
company:Acme Inc

@employees(2):active,department,id,name,skills
T,Engineering,1,John Doe,[Python,Go]
^,^,_,Jane Smith,[Java,Kotlin]
```

**Symbols explained**:
- `company:Acme Inc` → metadata (no quotes needed)
- `@employees(2)` → The table name and row count
- `T` → Boolean true
- `^` → Repeat "Engineering" and "T"
- `_` → Auto-increment ID (2 = 1 + 1)
- `[Python,Go]` → Inline array (no quotes)

- `[Python,Go]` → Inline array (no quotes)

### Nested Objects in Tables

**Input**:
```json
[
  {"id": 1, "meta": {"ip": "1.2.3.4", "agent": "Firefox"}},
  {"id": 2, "meta": {"ip": "10.0.0.1", "agent": "Chrome"}}
]
```

**ZON**:
```
@data(2):id,meta
1,"{agent:Firefox,ip:1.2.3.4}"
2,"{agent:Chrome,ip:10.0.0.1}"
```

- Nested objects use `{key:val}` syntax
- **Double-quoted** for CSV safety (`""` escapes quotes)
- Keys are unquoted if simple

---

### Repetitive Data

**Input**: Weather data with repeated locations

```json
[
  {"date": "2024-01-01", "city": "NYC", "temp": 32},
  {"date": "2024-01-02", "city": "NYC", "temp": 35},
  {"date": "2024-01-03", "city": "NYC", "temp": 30},
  {"date": "2024-01-04", "city": "LA", "temp": 68}
]
```

**ZON**:
```
@data(4):city,date,temp
NYC,2024-01-01,32
^,2024-01-02,35
^,2024-01-03,30
LA,2024-01-04,68
```

- `^` compresses 3 repeated "NYC" values
- Saves ~12 bytes on city names alone

---

### Mixed Data Types

**Input**:
```json
{
  "user": "alice",
  "score": 95.5,
  "verified": true,
  "tags": ["premium", "early-adopter"],
  "metadata": null
}
```

**ZON**:
```
metadata:null
score:95.5
tags:[premium,early-adopter]
user:alice
verified:T
```

- All types preserved correctly
- Alphabetical sorting for consistency
- No unnecessary quotes

---

## When to Quote Strings

ZON uses **minimal quoting** - quotes are only added when the value contains:
- Comma `,` (the delimiter)
- Newline, tab, or control characters
- Brackets `[]` that could be confused with arrays
- Quote character `"`

### Examples:

| Value | ZON Output | Quoted? | Reason |
|-------|------------|---------|--------|
| `Alice` | `Alice` | No | Simple alphanumeric |
| `New York` | `New York` | No | **Spaces are fine!** |
| `Hello: World` | `Hello: World` | No | **Colons are fine!** |
| `data,value` | `"data,value"` | Yes | Contains comma |
| `[test]` | `"[test]"` | Yes | Contains brackets |
| `say "hi"` | `"say ""hi"""` | Yes | Contains quotes |

This is a major improvement over v7.0 which quoted anything with spaces or colons!

---

## Performance Tips

1. **Use sequential IDs**: Let `_` token handle auto-increment
2. **Group similar data**: Repetition compression works best on sorted data
3. **Flatten when possible**: Nested objects become dot-notation metadata
4. **Avoid deep nesting in tables**: Tables should be flat records

---

## See Also

- [README.md](README.md) - Full documentation
- [benchmarks/encoded_samples/](benchmarks/encoded_samples/) - Real-world examples
