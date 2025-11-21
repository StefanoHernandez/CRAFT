# TOON Format in CRAFT

## What is TOON?

**TOON (Token-Oriented Object Notation)** is a compact, human-readable serialization format designed specifically for passing structured data to Large Language Models (LLMs). It reduces token usage by **30-60%** compared to JSON.

## Why TOON?

When working with LLMs, every token counts:
- **Lower costs**: Fewer tokens = lower API costs
- **Faster responses**: Less data to process
- **Better context**: More room for actual content
- **Human-readable**: Easy to read and debug

## TOON vs JSON

### Example: Array of Objects

**JSON** (verbose):
```json
[
  {"id": 1, "name": "Alice", "active": true},
  {"id": 2, "name": "Bob", "active": false},
  {"id": 3, "name": "Charlie", "active": true}
]
```
**Tokens**: ~40

**TOON** (compact):
```
[3,]{id,name,active}:
  1,Alice,true
  2,Bob,false
  3,Charlie,true
```
**Tokens**: ~15

**Savings**: 62.5% fewer tokens! 💰

## TOON in CRAFT

CRAFT automatically uses TOON format when:
1. Passing tool schemas to LLMs
2. Returning tool results
3. Sending structured data to agents

### Using TOON with Tools

```python
from craft.tools import tool

@tool
def get_users(department: str, active: bool = True) -> list:
    """Get users from a department."""
    return [
        {"id": 1, "name": "Alice", "role": "Engineer"},
        {"id": 2, "name": "Bob", "role": "Designer"},
    ]

# Tool automatically uses TOON format for LLM communication
# JSON: ~50 tokens
# TOON: ~20 tokens
# Savings: 60%!
```

### Format Selection

```python
# Get JSON schema (default)
schema = tool.to_function_schema(format="json")

# Get TOON-optimized schema (recommended for LLMs)
schema = tool.to_function_schema(format="toon")
```

## TOON Format Basics

### Primitive Arrays
```python
# Numbers
[5]: 1,2,3,4,5

# Strings
[3]: apple,banana,cherry

# Booleans
[3]: true,false,true

# Mixed
[5]: 1,two,true,null,3.14
```

### Tabular Arrays (Uniform Objects)
```python
# Automatic tabular format for uniform objects
[3,]{id,name,active}:
  1,Alice,true
  2,Bob,false
  3,Charlie,true
```

### Nested Objects
```python
user:
  name: Alice
  age: 30
  address:
    city: Boston
    zip: 02101
```

### Custom Delimiters
```python
# Comma (default)
[5]: 1,2,3,4,5

# Tab
[5	]: 1	2	3	4	5

# Pipe
[5|]: 1|2|3|4|5
```

## Installation

TOON support is included by default in CRAFT:

```bash
pip install craft-chatbot
```

The `python-toon` library is automatically installed as a dependency.

## Performance Benefits

### Real-world Example: Product Search

**Scenario**: Returning 10 products with 5 fields each

| Format | Tokens | Cost (GPT-4) | Savings |
|--------|--------|--------------|---------|
| JSON   | ~250   | $0.0075      | -       |
| TOON   | ~100   | $0.0030      | 60%     |

**Annual savings** (1M API calls): **$4,500** 💰

## Best Practices

1. **Use TOON for tool schemas**: Reduces prompt tokens
2. **Use TOON for tool results**: Reduces completion tokens
3. **Use TOON for structured data**: Any data sent to/from LLMs
4. **Keep JSON for APIs**: Use JSON for external APIs, TOON for LLMs

## Encoding/Decoding

```python
from toon import encode, decode

# Encode Python data to TOON
data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
toon_str = encode(data)
# Output: [2,]{id,name}:\n  1,Alice\n  2,Bob

# Decode TOON back to Python
decoded = decode(toon_str)
# Output: [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
```

## Configuration

```python
from toon import encode

# Custom options
encode(data, {
    "indent": 2,           # Spaces per indent
    "delimiter": ",",      # Delimiter: , | \t | |
    "lengthMarker": "#"    # Optional length marker
})
```

## Learn More

- **TOON Specification**: https://github.com/toon-format/toon
- **Python TOON**: https://github.com/xaviviro/python-toon
- **Token Calculator**: Compare JSON vs TOON token usage

## Summary

✅ **30-60% fewer tokens** than JSON  
✅ **Human-readable** format  
✅ **Automatic** in CRAFT  
✅ **Lower costs** for LLM APIs  
✅ **Better performance**  

**Use TOON for all LLM communication in CRAFT!** 🚀
