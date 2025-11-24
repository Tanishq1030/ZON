# ZON Protocol Constants v8.0 (ClearText)
VERSION = "8.0"

# Format markers
TABLE_MARKER = "@"          # @hikes(3): col1, col2
META_SEPARATOR = ":"        # key:value (no space for compactness)

# Stream Tokens
GAS_TOKEN = "_"             # Auto-increment token
LIQUID_TOKEN = "^"          # Repeat previous value

# Thresholds
DEFAULT_ANCHOR_INTERVAL = 50
SINGLETON_THRESHOLD = 1     # Flatten lists with 1 item to metadata
INLINE_THRESHOLD_ROWS = 0

# Legacy compatibility (kept for potential fallback)
DICT_REF_PREFIX = "%"
ANCHOR_PREFIX = "$"
REPEAT_SUFFIX = "x"
