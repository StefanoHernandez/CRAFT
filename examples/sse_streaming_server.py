"""
SSE Streaming Server Example

Demonstrates Server-Sent Events for agent streaming.
Works as a fallback when WebSocket is blocked.

Run: python examples/sse_streaming_server.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from craft.api.sse import create_sse_app, broadcast_to_sse
from craft.api.events import (
    get_global_emitter,
    emit_agent_start,
    emit_thought,
    emit_tool_call_start,
    emit_tool_call_end,
    emit_response_chunk,
    emit_agent_end
)
import uvicorn


async def simulate_agent_execution():
    """Simulate agent execution (same as WebSocket example)."""
    agent_name = "demo_agent"
    
    print("\n🤖 Simulating agent execution...")
    print("📡 Events will be streamed via SSE\n")
    
    await emit_agent_start(agent_name, "Calculate 15 * 24", max_steps=5)
    await asyncio.sleep(1)
    
    await emit_thought(agent_name, "I need to calculate 15 * 24", step_index=0)
    await asyncio.sleep(1)
    
    await emit_tool_call_start(agent_name, "calculator", {"operation": "multiply", "a": 15, "b": 24}, step_index=1)
    await asyncio.sleep(0.5)
    await emit_tool_call_end(agent_name, "calculator", result=360, success=True, step_index=1)
    await asyncio.sleep(1)
    
    await emit_thought(agent_name, "The result is 360", step_index=2)
    await asyncio.sleep(1)
    
    response = "The result of 15 × 24 is 360."
    for chunk in response.split():
        await emit_response_chunk(agent_name, chunk + " ", step_index=3)
        await asyncio.sleep(0.2)
    
    await asyncio.sleep(1)
    
    await emit_agent_end(agent_name, result="360", total_steps=4, execution_time=5.5)
    
    print("✅ Agent execution complete!\n")


async def run_demo_server():
    """Run SSE demo server."""
    print("=" * 60)
    print("🔄 CRAFT SSE Streaming Demo Server")
    print("=" * 60)
    print("\n📍 Server will start on: http://localhost:8001")
    print("📡 SSE endpoint: http://localhost:8001/sse/your-client-id")
    print("\n💡 SSE advantages:")
    print("  - Works over HTTP (firewall-friendly)")
    print("  - Auto-reconnect built-in")
    print("  - Browser native EventSource API")
    print("\n💡 Tips:")
    print("  - Use browser: const es = new EventSource('http://localhost:8001/sse/browser-client')")
    print("  - Or run: python examples/sse_client.py")
    print("  - Check stats: http://localhost:8001/sse/stats")
    print("\n⏳ Waiting for connections...")
    print("   (Will simulate agent in 10 seconds)\n")
    
    # Schedule simulations
    async def delayed_simulation():
        await asyncio.sleep(10)
        await simulate_agent_execution()
        
        while True:
            await asyncio.sleep(30)
            await simulate_agent_execution()
    
    asyncio.create_task(delayed_simulation())
    
    # Create and run app
    app = create_sse_app()
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(run_demo_server())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
