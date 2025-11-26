"""
Example: TOON vs JSON - Token Efficiency Comparison

This example demonstrates how TOON format reduces token usage by 30-60%
compared to JSON when passing structured data to LLMs.
"""

import json
from craft.tools import tool, ToolRegistry, set_global_registry

try:
    from toon import encode as toon_encode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    print("⚠️  python-toon not installed. Install with: pip install python-toon")


# Create registry
registry = ToolRegistry()
set_global_registry(registry)


@tool
def search_products(
    query: str,
    category: str = "all",
    min_price: float = 0.0,
    max_price: float = 1000.0,
    in_stock: bool = True
) -> list:
    """Search for products in the database with filters."""
    # Mock product data
    products = [
        {"id": 1, "name": "Laptop Pro", "price": 1299.99, "stock": 15, "category": "electronics"},
        {"id": 2, "name": "Wireless Mouse", "price": 29.99, "stock": 50, "category": "electronics"},
        {"id": 3, "name": "USB-C Cable", "price": 12.99, "stock": 100, "category": "accessories"},
        {"id": 4, "name": "Desk Lamp", "price": 45.00, "stock": 25, "category": "furniture"},
        {"id": 5, "name": "Notebook", "price": 8.99, "stock": 200, "category": "stationery"},
    ]
    
    # Filter products
    filtered = [
        p for p in products
        if (category == "all" or p["category"] == category)
        and min_price <= p["price"] <= max_price
        and (not in_stock or p["stock"] > 0)
        and query.lower() in p["name"].lower()
    ]
    
    return filtered


def compare_formats():
    """Compare JSON vs TOON format for tool schemas and data."""
    
    print("=" * 80)
    print("TOON vs JSON: Token Efficiency Comparison")
    print("=" * 80)
    
    # Get the tool
    tool_instance = search_products
    
    # 1. Tool Schema Comparison
    print("\n📋 TOOL SCHEMA COMPARISON\n")
    
    # JSON schema
    json_schema = tool_instance.to_function_schema(format="json")
    json_str = json.dumps(json_schema, indent=2)
    json_tokens = len(json_str.split())  # Rough token estimate
    
    print("JSON Schema:")
    print(json_str)
    print(f"\n📊 Estimated tokens: ~{json_tokens}")
    
    if TOON_AVAILABLE:
        # TOON schema
        toon_schema = tool_instance.to_function_schema(format="toon")
        toon_str = json.dumps(toon_schema, indent=2)
        toon_tokens = len(toon_str.split())
        
        print("\n" + "-" * 80)
        print("\nTOON Schema:")
        print(toon_str)
        print(f"\n📊 Estimated tokens: ~{toon_tokens}")
        
        savings = ((json_tokens - toon_tokens) / json_tokens) * 100
        print(f"\n💰 Token savings: {savings:.1f}%")
    
    # 2. Tool Result Comparison
    print("\n" + "=" * 80)
    print("\n📦 TOOL RESULT COMPARISON\n")
    
    # Execute tool
    results = search_products(query="laptop", category="electronics", max_price=1500.0)
    
    # JSON format
    json_result = json.dumps(results, indent=2)
    json_result_tokens = len(json_result.split())
    
    print("JSON Result:")
    print(json_result)
    print(f"\n📊 Estimated tokens: ~{json_result_tokens}")
    
    if TOON_AVAILABLE:
        # TOON format
        toon_result = toon_encode(results)
        toon_result_tokens = len(toon_result.split())
        
        print("\n" + "-" * 80)
        print("\nTOON Result:")
        print(toon_result)
        print(f"\n📊 Estimated tokens: ~{toon_result_tokens}")
        
        savings = ((json_result_tokens - toon_result_tokens) / json_result_tokens) * 100
        print(f"\n💰 Token savings: {savings:.1f}%")
    
    # 3. Summary
    print("\n" + "=" * 80)
    print("\n📈 SUMMARY\n")
    print("TOON format advantages:")
    print("  ✅ 30-60% fewer tokens than JSON")
    print("  ✅ Human-readable like YAML")
    print("  ✅ Tabular format for uniform arrays")
    print("  ✅ Optimized for LLM consumption")
    print("  ✅ Lower API costs (fewer tokens)")
    print("\nUse TOON for:")
    print("  • Tool schemas passed to LLMs")
    print("  • Tool results returned from functions")
    print("  • Any structured data sent to/from LLMs")
    print("=" * 80)


if __name__ == "__main__":
    compare_formats()
