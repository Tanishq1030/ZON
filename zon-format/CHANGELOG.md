# Changelog

All notable changes to the ZON Format project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-11-24

### Changed - "ClearText" Major Format Overhaul

#### Format Improvements
- **Removed protocol overhead**: Eliminated `#Z:`, `|` pipes, and complex header markers
- **YAML-like metadata**: Changed from `M=key="val"` to clean `key:val` syntax
- **Clean @table syntax**: Replaced schema markers with readable `@tablename(count):cols`
- **Aggressive quote removal**: Only quote when absolutely necessary (commas, control chars)
  - Spaces no longer trigger quoting: `Blue Lake Trail` instead of `"Blue Lake Trail"`
  - Colons allowed in values
- **Compact array syntax**: `[item1,item2,item3]` with minimal inner quotes
- **No spaces after separators**: Removed spaces after `:` and `,` for compactness

#### Performance
- **31.9% compression** vs JSON (up from 27.4%)
- **25.6% better** than TOON (up from 20.8%)
- Tested on 318 records across 6 real-world datasets

#### New Features
- Singleton bypass: 1-item lists flatten to metadata (`items.0.id:1`)
- Pure list handling: Lists without wrapper use default `@data` table name
- Boolean hard rule: Always explicit `T`/`F`, never inferred from empty cells

#### Documentation
- Comprehensive README.md with visual comparisons
- EXAMPLES.md with detailed symbol reference
- Benchmark sample generation scripts
- `/benchmarks/encoded_samples/` with `.json`, `.zon`, and `.toon` comparisons

### Fixed
- Boolean preservation in roundtrip encoding/decoding
- Array index handling in decoder unflatten logic
- Pure list encoding/decoding (was returning empty string)

## [1.0.0] - 2025-11-23

### Added - Initial Release

#### Core Features
- ZON v7.0 format with pipe-based protocol syntax
- Compression rules: Range (R), Liquid (L), Solid (S), Pattern (P), Value (V)
- Anchor-based row references
- Global dictionary for repeated strings
- CLI tool for encoding/decoding
- Comprehensive test suite

#### Performance
- ~27% average compression vs JSON
- ~21% better than TOON on structured data

#### Package
- Python 3.8+ support
- PyPI distribution
- Apache 2.0 license

---

## Upgrade Notes

### From 1.0.0 to 1.0.1

**⚠️ Breaking Change**: The encoded format has changed completely. Data encoded with v1.0.0 will **not** decode correctly with v1.0.1.

**Migration**: Re-encode your data with v1.0.1:

```python
import zon

# Load your JSON data
with open('data.json') as f:
    data = json.load(f)

# Encode with new format
encoded = zon.encode(data)

# Decode works as before
decoded = zon.decode(encoded)
```

**Benefits**: The new format is much more readable and efficient. The migration is worth it for:
- ✅ 4.5% additional compression
- ✅ Zero protocol overhead
- ✅ Better LLM readability
- ✅ Cleaner visual appearance

---

## Links

- [PyPI](https://pypi.org/project/zon-format/)
- [GitHub](https://github.com/ZON-Format/ZON)
- [Examples](EXAMPLES.md)
- [README](README.md)
