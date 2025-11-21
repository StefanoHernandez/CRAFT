"""Simple test to debug the decorator"""

from craft.tools.decorator import tool
from craft.tools.base import Tool

@tool
def test_func(x: str) -> str:
    """Test function"""
    return x

print(f"Type: {type(test_func)}")
print(f"Is Tool: {isinstance(test_func, Tool)}")
print(f"Name: {test_func.name if hasattr(test_func, 'name') else 'NO NAME'}")
print(f"Has metadata: {hasattr(test_func, 'metadata')}")

# Try calling it
result = test_func(x="hello")
print(f"Result: {result}")
