"""
Example: Using @tool decorator with MCP integration.

This example shows how to create custom tools using the @tool decorator
and how they automatically integrate with the MCP system.
"""

from craft.tools import tool, ToolRegistry, set_global_registry
from craft.providers import AnthropicProvider
from craft.core.chatbot import Chatbot


# Create global tool registry
registry = ToolRegistry()
set_global_registry(registry)


# Define tools using @tool decorator
# These are automatically registered with MCP
@tool
def get_weather(city: str, units: str = "celsius") -> str:
    """Get the current weather for a city."""
    # In a real implementation, this would call a weather API
    return f"The weather in {city} is sunny and 22°{units[0].upper()}"


@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    # Safe evaluation (in real implementation, use ast.literal_eval or similar)
    try:
        # This is a simplified example - use proper safe evaluation in production
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@tool(name="search_database", description="Search the product database")
def search_products(query: str, max_results: int = 5) -> list:
    """Search for products in the database."""
    # Mock implementation
    return [
        {"name": f"Product {i}", "price": 10.0 * i}
        for i in range(1, max_results + 1)
    ]


# Now use the tools with a chatbot
def main():
    # Create chatbot with provider
    chatbot = Chatbot(
        provider=AnthropicProvider(
            api_key="your-api-key",
            model="claude-sonnet-4.5"
        ),
        system_prompt="You are a helpful assistant with access to tools."
    )

    # The tools are already registered via @tool decorator
    print(f"Registered tools: {len(registry)}")
    print(f"Available tools: {[t.name for t in registry.list_tools()]}")

    # Tools can be called directly
    print("\nDirect tool calls:")
    print(get_weather("Rome"))
    print(calculate("2 + 2 * 3"))
    print(search_products("laptop", max_results=3))

    # Or used by the chatbot through MCP
    # (This would require agent integration which we'll implement next)
    print("\nTools are ready to be used by agents via MCP!")


if __name__ == "__main__":
    main()
