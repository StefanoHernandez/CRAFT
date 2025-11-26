"""Demo of the Context Tracing system."""

import asyncio
import os

# Enable tracing at verbose level
os.environ["CRAFT_TRACE_CLIENT_IO"] = "3"

from craft.tracing import tracer


async def simulate_agent_execution():
    """Simulate an agent execution with nested operations."""
    
    # Start trace
    tracer.start_trace("research_task")
    
    # Agent planning
    with tracer.span("agent.planning", query="What is quantum computing?"):
        await asyncio.sleep(0.1)
    
    # Tool calls
    with tracer.span("tool.web_search", query="quantum computing basics"):
        await asyncio.sleep(0.3)
    
    with tracer.span("tool.summarize", text="long article"):
        await asyncio.sleep(0.2)
    
    # Memory access
    with tracer.span("memory.search", query="previous research"):
        await asyncio.sleep(0.05)
    
    # Synthesis
    with tracer.span("agent.synthesis"):
        await asyncio.sleep(0.15)
    
    # End trace and print
    tracer.end_trace()


async def simulate_with_error():
    """Simulate an execution with an error."""
    
    tracer.start_trace("error_example")
    
    with tracer.span("agent.planning"):
        await asyncio.sleep(0.05)
    
    try:
        with tracer.span("tool.broken_api"):
            await asyncio.sleep(0.1)
            raise Exception("API connection failed")
    except Exception:
        pass  # Error captured in span
    
    tracer.end_trace()


async def simulate_nested_operations():
    """Simulate deeply nested operations."""
    
    tracer.start_trace("complex_workflow")
    
    with tracer.span("agent.run") as agent_span:
        await asyncio.sleep(0.05)
        
        with tracer.span("agent.planning"):
            await asyncio.sleep(0.1)
            
            # Nested tool call during planning
            with tracer.span("tool.calculator"):
                await asyncio.sleep(0.05)
        
        with tracer.span("agent.execution"):
            await asyncio.sleep(0.2)
            
            # Multiple tools in parallel (simulated)
            with tracer.span("tool.search"):
                await asyncio.sleep(0.15)
            
            with tracer.span("tool.summarize"):
                await asyncio.sleep(0.1)
    
    tracer.end_trace()


async def main():
    print("="*60)
    print("🔍 CRAFT Tracing System Demo")
    print("="*60)
    print()
    
    print("Example 1: Normal Execution")
    print("-"*60)
    await simulate_agent_execution()
    print()
    
    print("Example 2: Execution with Error")
    print("-"*60)
    await simulate_with_error()
    print()
    
    print("Example 3: Nested Operations")
    print("-"*60)
    await simulate_nested_operations()
    print()
    
    print("="*60)
    print("✅ Demo completed!")
    print()
    print("💡 Try different trace levels:")
    print("   export CRAFT_TRACE_CLIENT_IO=0  # Disabled")
    print("   export CRAFT_TRACE_CLIENT_IO=1  # Basic")
    print("   export CRAFT_TRACE_CLIENT_IO=2  # Detailed")
    print("   export CRAFT_TRACE_CLIENT_IO=3  # Verbose")


if __name__ == "__main__":
    asyncio.run(main())
