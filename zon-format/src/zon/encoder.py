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
                
                # Repetition detection
                if i > 0 and val == prev_vals[col] and analysis['has_repetition']:
                    tokens.append(LIQUID_TOKEN)
                    prev_vals[col] = val
                    continue
                
                # Explicit value
                tokens.append(self._format_value(val))
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
        if isinstance(val, list):
            # Format list with minimal quoting: [item1,item2,item3]
            items = []
            for item in val:
                if isinstance(item, str):
                    # Only quote if contains comma, brackets, or control chars
                    if any(c in item for c in [',', '[', ']', '\n', '\r', '\t']):
                        items.append(json.dumps(item))
                    else:
                        items.append(item)
                else:
                    items.append(self._format_value(item))
            # Lists contain commas, so quote the whole thing for CSV
            list_str = f"[{','.join(items)}]"
            return json.dumps(list_str)  # Quote for CSV safety
        if isinstance(val, dict):
            # Dict as JSON - MUST be quoted for CSV (contains commas)
            json_str = json.dumps(val, separators=(',', ':'))
            return json.dumps(json_str)  # Double-encode: first to JSON, then quote for CSV
        
        # String formatting with minimal quoting
        s = str(val)
        if self._needs_quotes(s):
            return json.dumps(s)
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
