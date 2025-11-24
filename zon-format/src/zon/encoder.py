"""
ZON Encoder v8.0 - ClearText Format

This encoder produces clean, document-style output with YAML-like metadata
and CSV-like tables using @table syntax.
"""

import json
import re
import csv
import io
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
from .constants import *


class ZonEncoder:
    def __init__(self, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL):
        self.anchor_interval = anchor_interval
        self._safe_str_re = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    def encode(self, data: Any) -> str:
        """
        Encode data to ZON v8.0 ClearText format.
        
        Args:
            data: Input data (list or dict)
            
        Returns:
            ZON-encoded string in ClearText format
        """
        # 1. Root Promotion: Separate metadata from stream
        stream_data, metadata, stream_key = self._extract_primary_stream(data)
        
        # Fallback for simple/empty data
        if not stream_data and not metadata:
            return json.dumps(data, separators=(',', ':'))

        output = []
        
        # If stream_key is None (pure list input), use default key
        if stream_data and stream_key is None:
            stream_key = "data"
        
        # 2. Singleton Bypass: Flatten 1-item lists to metadata
        # DISABLED: Conflicts with depth-limited flattening
        # TODO: Fix singleton bypass to work with depth limits
        # if stream_data and len(stream_data) == 1 and stream_key:
        #     # Flatten the single item into metadata with index notation
        #     item = stream_data[0]
        #     if isinstance(item, dict):
        #         flattened = self._flatten(item, parent=f"{stream_key}.0")
        #         metadata.update(flattened)
        #         stream_data = None
        
        # 3. Write Metadata (YAML-like)
        if metadata:
            output.extend(self._write_metadata(metadata))
        
        # 4. Write Table (if multi-item stream exists)
        if stream_data and stream_key:
            if output:  # Add blank line separator
                output.append("")
            output.extend(self._write_table(stream_data, stream_key))
        
        return "\n".join(output)

    def _extract_primary_stream(self, data) -> Tuple[Optional[List], Dict, Optional[str]]:
        """
        Root Promotion Algorithm: Find the main table in the JSON.
        
        Args:
            data: Input data
            
        Returns:
            (stream_data, metadata, stream_key)
        """
        if isinstance(data, list):
            return data, {}, None  # stream_key is None for pure lists
        
        if isinstance(data, dict):
            # Find largest list of objects
            candidates = []
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0:
                    # Check if list contains objects (tabular candidate)
                    if isinstance(v[0], dict):
                        # Score = Rows * Cols
                        score = len(v) * len(v[0].keys())
                        candidates.append((k, v, score))
            
            if candidates:
                candidates.sort(key=lambda x: x[2], reverse=True)
                key, stream, _ = candidates[0]
                meta = {k: v for k, v in data.items() if k != key}
                return stream, meta, key
        
        return None, data if isinstance(data, dict) else {}, None

    def _write_metadata(self, metadata: Dict) -> List[str]:
        """
        Write metadata in YAML-like format.
        
        Args:
            metadata: Dictionary of metadata
            
        Returns:
            List of formatted lines
        """
        lines = []
        flattened = self._flatten(metadata)
        
        for key, value in sorted(flattened.items()):
            val_str = self._format_value(value)
            lines.append(f"{key}{META_SEPARATOR}{val_str}")
        
        return lines

    def _write_table(self, stream: List[Dict], key: str) -> List[str]:
        """
        Write table in @table format with compression.
        
        Args:
            stream: List of records
            key: Table name
            
        Returns:
            List of formatted lines
        """
        if not stream:
            return []
        
        lines = []
        
        # Flatten all rows
        flat_stream = [self._flatten(row) for row in stream]
        
        # Get column names
        all_keys = set().union(*(d.keys() for d in flat_stream))
        cols = sorted(list(all_keys))
        
        # Analyze columns for compression
        col_analysis = self._analyze_columns(flat_stream, cols)
        
        # Write table header
        col_names = ",".join(cols)  # No space after comma for compactness
        lines.append(f"{TABLE_MARKER}{key}({len(stream)}){META_SEPARATOR}{col_names}")
        
        # Write rows
        prev_vals = {col: None for col in cols}
        
        for i, row in enumerate(flat_stream):
            tokens = []
            
            for col in cols:
                val = row.get(col)
                analysis = col_analysis[col]
                
                # Auto-increment detection for first column (usually ID)
                if col == cols[0] and analysis['is_sequential'] and i > 0:
                    # Use _ for sequential IDs after first
                    if val == prev_vals[col] + analysis['step']:
                        tokens.append(GAS_TOKEN)
                        prev_vals[col] = val
                        continue
                
                # Explicit value
                formatted_val = self._format_value(val)
                
                # Repetition detection
                # Only use ^ if it saves space (length > 1)
                if i > 0 and val == prev_vals[col] and analysis['has_repetition'] and len(formatted_val) > 1:
                    tokens.append(LIQUID_TOKEN)
                else:
                    tokens.append(formatted_val)
                
                prev_vals[col] = val
            
            lines.append(",".join(tokens))  # No space after comma for compactness
        
        return lines

    def _analyze_columns(self, data: List[Dict], cols: List[str]) -> Dict:
        """
        Analyze columns for compression opportunities.
        
        Args:
            data: Flattened stream data
            cols: Column names
            
        Returns:
            Dictionary of column analysis
        """
        analysis = {}
        
        for col in cols:
            vals = [d.get(col) for d in data]
            
            result = {
                'is_sequential': False,
                'step': 1,
                'has_repetition': False
            }
            
            # Check for sequential numbers
            nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if len(nums) == len(vals) and len(vals) > 1:
                try:
                    diffs = [nums[i] - nums[i-1] for i in range(1, len(nums))]
                    if len(set(diffs)) == 1:
                        result['is_sequential'] = True
                        result['step'] = diffs[0]
                except:
                    pass
            
            # Check for repetition
            if len(vals) > 1:
                try:
                    unique_count = len(set(json.dumps(v, sort_keys=True) for v in vals))
                    if unique_count < len(vals):
                        result['has_repetition'] = True
                except:
                    pass
            
            analysis[col] = result
        
        return analysis

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
    def _csv_quote(self, s: str) -> str:
        """
        Quote a string for CSV (RFC 4180).
        
        Escapes quotes by doubling them (" -> "") and wraps in double quotes.
        """
        escaped = s.replace('"', '""')
        return f'"{escaped}"'

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
    def _format_zon_node(self, val: Any) -> str:
        """
        Format a value using ZON-style syntax for nested structures.
        Dicts: {key:val,key:val}
        Lists: [val,val]
        Strings: Minimal quoting
        """
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, (int, float)):
            s = str(val)
            return s[:-2] if s.endswith(".0") else s
        
        if isinstance(val, dict):
            items = []
            # Sort keys for consistent output
            for k, v in sorted(val.items()):
                # Format key (unquoted if simple)
                key_str = k
                if self._needs_quotes(k):
                    key_str = self._csv_quote(k)
                
                # Format value recursively
                val_str = self._format_zon_node(v)
                items.append(f"{key_str}:{val_str}")
            return f"{{{','.join(items)}}}"
            
        if isinstance(val, list):
            items = [self._format_zon_node(item) for item in val]
            return f"[{','.join(items)}]"
            
        # String handling
        s = str(val)
        # For nested ZON nodes, we need to be careful about delimiters
        # The delimiters are ',' (item sep), ':' (kv sep), '}' (dict end), ']' (list end)
        # We reuse _needs_quotes but might need stricter rules for nested context?
        # Actually, if we use standard CSV quoting for the *outer* cell, 
        # then inside the cell we just need to ensure we don't break the ZON parser.
        # The ZON parser will look for , : } ]
        if any(c in s for c in [',', ':', '{', '}', '[', ']']):
             # Use JSON-style quoting for inner strings to avoid confusion with CSV quotes
             # But wait, we want to avoid \" escaping if possible.
             # Let's stick to standard quoting but we need to escape the quote char itself.
             # If we use "..." for strings, we need to escape " inside.
             return json.dumps(s)
        return s

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, bool):
            return "T" if val else "F"
        if isinstance(val, (int, float)):
            s = str(val)
            # Remove .0 suffix for cleaner output
            return s[:-2] if s.endswith(".0") else s
        
        if isinstance(val, (list, dict)):
            # Use ZON-style formatting for complex types
            # This returns a string like "{k:v}" or "[a,b]"
            # This string might contain commas, so the WHOLE thing needs to be CSV-quoted
            zon_str = self._format_zon_node(val)
            if self._needs_quotes(zon_str):
                return self._csv_quote(zon_str)
            return zon_str
        
        # String formatting
        s = str(val)
        
        # Check if it looks like a number/bool/null (needs type protection)
        # These must be encoded as JSON strings ("...") so decoder sees quotes
        needs_type_protection = False
        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            needs_type_protection = True
        elif s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            needs_type_protection = True
        elif s.strip() != s: # Leading/trailing whitespace
            needs_type_protection = True
        else:
            try:
                float(s)
                needs_type_protection = True
            except ValueError:
                pass
                
        if needs_type_protection:
            # Wrap in quotes (JSON style) then CSV quote
            # s="123" -> json='"123"' -> csv='"""123"""'
            return self._csv_quote(json.dumps(s))
            
        # Check if it needs CSV quoting (delimiters)
        if self._needs_quotes(s):
            return self._csv_quote(s)
            
        return s

    def _needs_quotes(self, s: str) -> bool:
        """
        Determine if a string needs quotes.
        
        Minimal quoting rules:
        - Quote only if contains comma (the delimiter)
        - Quote if contains newline, tab, or quote char
        - Quote if is a reserved token (T, F, null, _, ^)
        
        Spaces, colons, and other chars are fine without quotes.
        
        Args:
            s: String to check
            
        Returns:
            True if quotes needed
        """
        if not s:
            return True
        
        # Reserved tokens need quoting
        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            return True
        
        # Quote if it looks like a number (to preserve string type)
        # Check for integer
        if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            return True
        # Check for float
        try:
            float(s)
            return True
        except ValueError:
            pass
            
        # Quote if leading/trailing whitespace (preserved)
        if s.strip() != s:
            return True
        
        # Only quote if contains delimiter or control chars
        if any(c in s for c in [',', '\n', '\r', '\t', '"', '[', ']']):
            return True
        
        return False

    def _flatten(self, d: Any, parent: str = '', sep: str = '.', max_depth: int = 1, current_depth: int = 0) -> Dict:
        """
        Flatten nested dictionary with depth limit.
        
        Only flattens up to max_depth levels to prevent unreadable 100+ column tables.
        Nested objects beyond max_depth are kept as inline JSON.
        
        Args:
            d: Data to flatten
            parent: Parent key prefix
            sep: Separator for keys
            max_depth: Maximum flattening depth (1 = only top level)
            current_depth: Current recursion depth (internal)
            
        Returns:
            Flattened dictionary
        """
        if not isinstance(d, dict):
            return {parent: d} if parent else {}
        
        items = []
        for k, v in d.items():
            new_key = f"{parent}{sep}{k}" if parent else k
            
            # DEPTH LIMIT: Stop flattening beyond max_depth
            if isinstance(v, dict) and current_depth < max_depth:
                # Recursively flatten this level
                items.extend(self._flatten(v, new_key, sep, max_depth, current_depth + 1).items())
            else:
                # Keep as-is: primitives or objects beyond depth limit
                items.append((new_key, v))
        
        return dict(items)


def encode(data: Any, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL) -> str:
    """
    Convenience function to encode data to ZON v8.0 format.
    
    Args:
        data: Input data
        anchor_interval: Interval for anchor rows (legacy, unused in v8.0)
        
    Returns:
        ZON-encoded string in ClearText format
    """
    return ZonEncoder(anchor_interval).encode(data)
