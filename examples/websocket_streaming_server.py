"""
Example: WebSocket Streaming with CRAFT Agents

This example demonstrates how to use WebSocket streaming to monitor
agent execution in real-time.

Run this example:
1. Start the WebSocket server: python examples/websocket_streaming_server.py
2. In another terminal, run the agent: python examples/websocket_streaming_client.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from craft.api.websocket import run_server, manager
from craft.api.events import (
    get_global_emitter,
    emit_agent_start,
    emit_thought,
    emit_tool_call_start,
    emit_tool_call_end,
    emit_response_chunk,
    emit_agent_end
)


async def simulate_agent_execution():
    """
    Simulate agent execution with events.
    
    In a real scenario, these events would be emitted by the Agent class
    during execution.
    """
    agent_name = "demo_agent"
    
    print("\n🤖 Simulating agent execution...")
    print("📡 Events will be streamed to WebSocket clients\n")
    
    # Start
    await emit_agent_start(agent_name, "Calculate 15 * 24 and explain", max_steps=5)
    await asyncio.sleep(1)
    
    # Thought
    await emit_thought(agent_name, "I need to calculate 15 * 24. I should use a calculator tool.", step_index=0)
    await asyncio.sleep(1)
    
    # Tool call
    await emit_tool_call_start(agent_name, "calculator", {"operation": "multiply", "a": 15, "b": 24}, step_index=1)
    await asyncio.sleep(0.5)
    await emit_tool_call_end(agent_name, "calculator", result=360, success=True, step_index=1)
    await asyncio.sleep(1)
    
    # Another thought
    await emit_thought(agent_name, "The calculation result is 360. Now I'll explain the process.", step_index=2)
    await asyncio.sleep(1)
    
    # Response chunks (streaming)
    response = "The result of 15 × 24 is 360. "
    for i, chunk in enumerate(response.split()):
        await emit_response_chunk(agent_name, chunk + " ", is_final=(i == len(response.split()) - 1), step_index=3)
        await asyncio.sleep(0.2)
    
    await asyncio.sleep(0.5)
    
    explanation = "This can be calculated as (15 × 20) + (15 × 4) = 300 + 60 = 360."
    for i, chunk in enumerate(explanation.split()):
        await emit_response_chunk(agent_name, chunk + " ", is_final=(i == len(explanation.split()) - 1), step_index=3)
        await asyncio.sleep(0.2)
    
    await asyncio.sleep(1)
    
    # End
    await emit_agent_end(agent_name, result="360", total_steps=4, execution_time=5.5)
    
    print("\n✅ Agent execution complete!")
    print(f"📊 Active connections: {len(manager.active_connections)}\n")


async def run_demo_server():
    """Run demo server with simulated agent."""
    print("=" * 60)
    print("🚀 CRAFT WebSocket Streaming Demo Server")
    print("=" * 60)
    print("\n📍 Server will start on: ws://localhost:8000")
    print("📡 Connect with: ws://localhost:8000/ws/your-client-id")
    print("\n💡 Tips:")
    print("  - Use browser DevTools WebSocket tab")
    print("  - Or run: python examples/websocket_client.py")
    print("  - Check stats: http://localhost:8000/stats")
    print("\n⏳ Waiting for connections...")
    print("   (Will simulate agent execution in 10 seconds)\n")
    
    # Schedule agent simulation
    async def delayed_simulation():
        await asyncio.sleep(10)
        await simulate_agent_execution()
        
        # Repeat every 30 seconds
        while True:
            await asyncio.sleep(30)
            await simulate_agent_execution()
    
    asyncio.create_task(delayed_simulation())
    
    # Run server (blocking)
    from craft.api.websocket import create_websocket_app, broadcast_agent_events
    import uvicorn
    
    app = create_websocket_app()
    emitter = get_global_emitter()
    
    @app.on_event("startup")
    async def startup():
        asyncio.create_task(broadcast_agent_events(emitter))
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(run_demo_server())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
