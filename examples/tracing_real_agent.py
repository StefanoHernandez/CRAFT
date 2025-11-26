"""Demo of tracing with a real Agent."""

import os
import asyncio
from craft.agents import Agent
from craft.agents import Agent
from craft.providers.base import Provider, ChatResponse, Role
from craft.tools.base import Tool, ToolMetadata, ToolParameter

# Enable tracing
os.environ["CRAFT_TRACE_CLIENT_IO"] = "3"

class MockProvider(Provider):
    """Mock provider for demo."""
    def __init__(self, responses=None):
        self._responses = responses or ["I should check the weather.", "The weather is sunny.", "Final answer: It is sunny."]
        self._call_count = 0
    
    @property
    def name(self) -> str:
        return "mock"
    
    def _validate_config(self) -> None:
        pass
    
    def chat(self, messages, stream=False, **kwargs):
        response = self._responses[min(self._call_count, len(self._responses) - 1)]
        self._call_count += 1
        return ChatResponse(content=response, role=Role.ASSISTANT, model="mock")
    
    async def achat(self, messages, stream=False, **kwargs):
        return self.chat(messages, stream, **kwargs)

def create_mock_tool():
    """Create a mock tool for testing."""
    def weather_func(location: str) -> str:
        return f"The weather in {location} is sunny and 25°C"
    
    metadata = ToolMetadata(
        name="get_weather",
        description="Get weather for a location",
        parameters=[
            ToolParameter(name="location", type="str", description="City name")
        ],
        return_type="str",
        json_schema={"type": "function", "function": {"name": "get_weather"}}
    )
    
    return Tool(
        name="get_weather",
        description="Get weather",
        func=weather_func,
        metadata=metadata
    )

async def main():
    print("="*60)
    print("🔍 CRAFT Real Agent Tracing Demo")
    print("="*60)
    
    # Setup
    tool = create_mock_tool()
    
    # Mock provider that simulates a conversation using the tool
    provider = MockProvider()
    # Mock responses: 
    # 1. Thought: I should check weather. Call tool.
    # 2. (Tool output injected)
    # 3. Final answer.
    # Note: MockProvider in craft/providers/base.py might be simple.
    # Let's use the one from craft.providers.mock if it exists, or base.
    # Actually, craft.providers doesn't export MockProvider directly in __init__.py usually?
    # Let's check imports.
    
    # Manually execute the tool to demonstrate tracing
    print("\nExecuting tool manually...")
    result = tool(location="London")
    print(f"Tool Result: {result}")
    
    # Run agent (will show agent trace)
    print("\nRunning agent...")
    agent = Agent(
        name="demo_agent",
        provider=provider,
        tools=[tool],
        verbose=True
    )
    
    # We need to start a trace manually for the tool call if we want it to be part of a trace
    # But Tool.__call__ starts its own span.
    # If there is no active trace, it might start a root span?
    # No, CraftTracer.span requires an active trace context or it might fail/do nothing if disabled?
    # CraftTracer.span checks self.enabled.
    # If CRAFT_TRACE_CLIENT_IO is set, it is enabled.
    # But start_trace must be called to create a context.
    # If no context, span() might raise error or create a temporary one?
    # Let's check tracer.py.
    
    # tracer.span() implementation:
    # if not self.enabled: yield None; return
    # if not self._current_context: ...
    
    # So we need to start a trace.
    from craft.tracing import tracer
    tracer.start_trace("manual_tool_demo")
    
    try:
        # 1. Manual tool call
        print("1. Calling tool directly:")
        tool(location="Paris")
        
        # 2. Agent run (starts its own trace internally? No, agent.run starts a trace!)
        # If agent.run starts a trace, it overwrites the current one?
        # Agent.run calls tracer.start_trace("agent.name").
        # start_trace overwrites _current_context.
        # So we should NOT wrap agent.run in another trace if we want to see agent's trace as root.
        pass
    finally:
        tracer.end_trace()
        
    print("\n2. Running Agent (starts its own trace):")
    # Agent.run will start "agent.demo_agent" trace
    agent.run("What is the weather?")

if __name__ == "__main__":
    asyncio.run(main())
