"""Example: Using custom tools with CRAFT."""

import os
from datetime import datetime
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.core.tool_calling import ToolCallingMixin


# Extend Chatbot with tool calling
class ToolEnabledChatbot(Chatbot, ToolCallingMixin):
    """Chatbot with tool calling capabilities."""

    def __init__(self, *args, **kwargs):
        Chatbot.__init__(self, *args, **kwargs)
        ToolCallingMixin.__init__(self)


# Define custom tools
def get_current_time(timezone: str = "UTC") -> str:
    """Get current time in specified timezone."""
    now = datetime.now()
    return f"Current time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"


def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Safe eval for basic math
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_weather(location: str) -> str:
    """Get weather for a location (mock implementation)."""
    # In production, this would call a real weather API
    return f"Weather in {location}: Sunny, 72°F, Humidity: 45%"


def main():
    print("🛠️  CRAFT Custom Tools Example\n")

    # Create tool-enabled chatbot
    chatbot = ToolEnabledChatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        system_prompt="You are a helpful assistant with access to tools. Use them when needed.",
    )

    # Register custom tools
    print("Registering custom tools...")

    chatbot.add_custom_tool(
        name="get_current_time",
        func=get_current_time,
        description="Get the current time in a specified timezone",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., UTC, EST, PST)",
                    "default": "UTC",
                }
            },
        },
    )

    chatbot.add_custom_tool(
        name="calculate",
        func=calculate,
        description="Calculate the result of a mathematical expression",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')",
                }
            },
            "required": ["expression"],
        },
    )

    chatbot.add_custom_tool(
        name="get_weather",
        func=get_weather,
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location",
                }
            },
            "required": ["location"],
        },
    )

    print(f"✓ Registered {len(chatbot.get_available_tools())} tools\n")

    # List available tools
    print("Available Tools:")
    for tool_schema in chatbot.get_available_tools():
        print(f"  - {tool_schema['name']}: {tool_schema['description']}")

    print("\n" + "=" * 60)
    print("Demo: Using tools manually")
    print("=" * 60 + "\n")

    # Demonstrate tool execution
    import asyncio

    async def demo():
        # Execute time tool
        print("1. Getting current time...")
        result = await chatbot.execute_tool("get_current_time", {"timezone": "UTC"})
        if result.success:
            print(f"   ✓ {result.result}\n")

        # Execute calculator tool
        print("2. Calculating 42 * 1337...")
        result = await chatbot.execute_tool("calculate", {"expression": "42 * 1337"})
        if result.success:
            print(f"   ✓ {result.result}\n")

        # Execute weather tool
        print("3. Getting weather for San Francisco...")
        result = await chatbot.execute_tool("get_weather", {"location": "San Francisco"})
        if result.success:
            print(f"   ✓ {result.result}\n")

    asyncio.run(demo())

    print("=" * 60)
    print("\n💡 In production, the LLM provider would decide when to call these tools")
    print("   based on the conversation context (function calling feature).")
    print("\n✨ Tools can be used to extend chatbot capabilities infinitely!")


if __name__ == "__main__":
    main()
