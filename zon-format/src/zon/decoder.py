"""
ZON Decoder v8.0 - ClearText Format

This decoder parses clean, document-style ZON with YAML-like metadata
and CSV-like tables using @table syntax.
"""

import json
import re
import csv
import io
from typing import List, Dict, Any, Optional
from .constants import *
from .exceptions import ZonDecodeError


class ZonDecoder:
    def decode(self, zon_str: str) -> Any:
        """
        Decode ZON v8.0 ClearText format to original data structure.
        
        Args:
            zon_str: ZON-encoded string
            
        Returns:
            Decoded data (list or dict)
        """
        if not zon_str:
            return {}
        
        lines = zon_str.strip().split('\n')
        if not lines:
            return {}
        
        metadata = {}
        tables = {}
        current_table = None
        current_table_name = None
        
        for line in lines:
            line = line.rstrip()
            
            # Skip blank lines
            if not line:
                continue
            
            # Table header: @hikes(2): id, name, sunny
            if line.startswith(TABLE_MARKER):
                current_table_name, current_table = self._parse_table_header(line)
                tables[current_table_name] = current_table
            
            # Table row (if we're in a table and haven't read all rows)
            elif current_table is not None and current_table['row_index'] < current_table['expected_rows']:
                row = self._parse_table_row(line, current_table)
                current_table['rows'].append(row)
                
                # If we've read all rows, exit table mode
                if current_table['row_index'] >= current_table['expected_rows']:
                    current_table = None
            
            # Metadata line: key: value
            elif META_SEPARATOR in line:
                current_table = None  # Exit table mode (safety)
                key, val = line.split(META_SEPARATOR, 1)
                metadata[key.strip()] = self._parse_value(val.strip())
        
        # Recombine tables into metadata
        for table_name, table in tables.items():
            metadata[table_name] = self._reconstruct_table(table)
        
        # Unflatten dotted keys
        result = self._unflatten(metadata)
        
        # Unwrap pure lists: if only key is 'data', return the list directly
        if len(result) == 1 and 'data' in result and isinstance(result['data'], list):
            return result['data']
        
        return result

    def _parse_table_header(self, line: str) -> tuple:
        """
        Parse table header line.
        
        Format: @tablename(count): col1, col2, col3
        
        Args:
            line: Header line
            
        Returns:
            (table_name, table_info dict)
        """
        # Extract: @hikes(2): id, name, sunny
        match = re.match(r'^' + re.escape(TABLE_MARKER) + r'(\w+)\((\d+)\)' + re.escape(META_SEPARATOR) + r'(.+)$', line)
        if not match:
            raise ZonDecodeError(f"Invalid table header: {line}")
        
        table_name = match.group(1)
        count = int(match.group(2))
        cols_str = match.group(3)
        
        # Parse column names
        cols = [c.strip() for c in cols_str.split(',')]
        
        return table_name, {
            'cols': cols,
            'rows': [],
            'prev_vals': {col: None for col in cols},
            'row_index': 0,
            'expected_rows': count
        }

    def _parse_table_row(self, line: str, table: Dict) -> Dict:
        """
        Parse a table row with compression token support.
        
        Args:
            line: Row line (CSV format)
            table: Table info from header
            
        Returns:
            Decoded row dictionary
        """
        # Parse CSV tokens
        tokens = list(csv.reader([line]))[0]
        
        # Pad if needed
        while len(tokens) < len(table['cols']):
            tokens.append('')
        
        row = {}
        prev_vals = table['prev_vals']
        row_idx = table['row_index']
        
        for i, (col, tok) in enumerate(zip(table['cols'], tokens)):
            val = None
            
            if tok == GAS_TOKEN:
                # Auto-increment: use previous + 1
                if prev_vals[col] is not None and isinstance(prev_vals[col], (int, float)):
                    val = prev_vals[col] + 1
                else:
                    val = row_idx + 1
            
            elif tok == LIQUID_TOKEN:
                # Repeat: use previous value
                val = prev_vals[col]
            
            else:
                # Explicit value
                val = self._parse_value(tok)
            
            row[col] = val
            prev_vals[col] = val
        
        table['row_index'] += 1
        return row

    def _reconstruct_table(self, table: Dict) -> List[Dict]:
        """
        Reconstruct table from parsed rows.
        
        Args:
            table: Table info with rows
            
        Returns:
            List of dictionaries
        """
        return [self._unflatten(row) for row in table['rows']]

    def _parse_zon_node(self, text: str) -> Any:
        """
        Parse a ZON-style nested structure: {k:v,k:v} or [v,v].
        Recursive descent parser.
        """
        text = text.strip()
        if not text:
            return None
            
        # Simple values
        if text == 'T': return True
        if text == 'F': return False
        if text == 'null': return None
        if text.isdigit(): return int(text)
        try:
            return float(text)
        except ValueError:
            pass
            
        # Quoted string (JSON style)
        if text.startswith('"'):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text # Fallback
        
        # List: [item1,item2]
        if text.startswith('[') and text.endswith(']'):
            content = text[1:-1]
            if not content.strip():
                return []
            
            items = []
            depth = 0
            current_item = []
            in_quote = False
            
            for char in content:
                if char == '"' and (not current_item or current_item[-1] != '\\'):
                    in_quote = not in_quote
                
                if not in_quote:
                    if char in '[{':
                        depth += 1
                    elif char in ']}':
                        depth -= 1
                    elif char == ',' and depth == 0:
                        items.append(self._parse_zon_node("".join(current_item)))
                        current_item = []
                        continue
                
                current_item.append(char)
            
            if current_item:
                items.append(self._parse_zon_node("".join(current_item)))
            return items

        # Dict: {k:v,k:v}
        if text.startswith('{') and text.endswith('}'):
            content = text[1:-1]
            if not content.strip():
                return {}
                
            items = {}
            depth = 0
            current_part = []
            current_key = None
            in_quote = False
            
            for char in content:
                if char == '"' and (not current_part or current_part[-1] != '\\'):
                    in_quote = not in_quote
                
                if not in_quote:
                    if char in '[{':
                        depth += 1
                    elif char in ']}':
                        depth -= 1
                    elif char == ':' and depth == 0 and current_key is None:
                        # Found key separator
                        key_str = "".join(current_part).strip()
                        # Unquote key if needed
                        if key_str.startswith('"'):
                            try:
                                current_key = json.loads(key_str)
                            except:
                                current_key = key_str
                        else:
                            current_key = key_str
                        current_part = []
                        continue
                    elif char == ',' and depth == 0:
                        # Found item separator
                        if current_key is not None:
                            val_str = "".join(current_part)
                            items[current_key] = self._parse_zon_node(val_str)
                            current_key = None
                            current_part = []
                        continue
                
                current_part.append(char)
            
            # Last item
            if current_key is not None:
                val_str = "".join(current_part)
                items[current_key] = self._parse_zon_node(val_str)
                
            return items

        # Unquoted string
        return text

    def _parse_value(self, val: str) -> Any:
        """
        Parse a single value from a ZON cell.
        """
        val = val.strip()
        if not val:
            return None
        if val == 'T':
            return True
        if val == 'F':
            return False
        if val == 'null':
            return None
        
        # Check for ZON-style nested structures
        # These will be unquoted here because the CSV parser already handled the outer quotes
        if (val.startswith('{') and val.endswith('}')) or (val.startswith('[') and val.endswith(']')):
            return self._parse_zon_node(val)
            
        # Try number
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except ValueError:
            pass
            
        # Double-encoded JSON string fallback (legacy support or explicit JSON)
        if val.startswith('"') and val.endswith('"'):
             try:
                 # It might be a JSON string that was double-quoted
                 # e.g. "foo,bar" -> CSV: """foo,bar""" -> unquoted: "foo,bar"
                 # If it looks like a JSON string, try to parse it
                 return json.loads(val)
             except json.JSONDecodeError:
                 pass

        return val

    def _unflatten(self, d: Dict) -> Dict:
        """
        Unflatten dictionary with dotted keys.
        
        Works with depth-limited flattening - handles both:
        - Dot notation: "meta.timestamp" -> {"meta": {"timestamp": ...}}
        - JSON objects: "meta.context" with value {"ip": "...", "user_agent": "..."}
        - Array indices: "items.0.id" -> {"items": [{"id": ...}]}
        
        Args:
            d: Flattened dictionary
            
        Returns:
            Nested dictionary
        """
        result = {}
        
        for key, value in d.items():
            # Check if key has dot notation
            if '.' not in key:
                # Simple key, just assign
                result[key] = value
                continue
                
            parts = key.split('.')
            target = result
            
            # Navigate/create nested structure
            for i, part in enumerate(parts[:-1]):
                next_part = parts[i + 1]
                
                # Check if next part is a number (array index)
                if next_part.isdigit():
                    idx = int(next_part)
                    
                    # Create array if needed
                    if part not in target:
                        target[part] = []
                    
                    # Extend array to accommodate index
                    while len(target[part]) <= idx:
                        target[part].append({})
                    
                    # Move into the indexed element
                    target = target[part][idx]
                    # Skip the numeric index in the path
                    parts.pop(i + 1)
                    break
                else:
                    # Regular nested object
                    if part not in target:
                        target[part] = {}
                    
                    # Only navigate deeper if it's a dict (not an already-parsed JSON object)
                    if isinstance(target[part], dict):
                        target = target[part]
                    else:
                        # Already has a value, can't navigate deeper
                        break
            
            # Set the final value
            final_key = parts[-1]
            if not final_key.isdigit():  # Don't use numeric index as key
                target[final_key] = value
        
        return result


def decode(data: str) -> Any:
    """
    Convenience function to decode ZON v8.0 format to original data.
    
    Args:
        data: ZON-encoded string
        
    Returns:
        Decoded data
    """
    return ZonDecoder().decode(data)
