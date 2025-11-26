"""
SSE (Server-Sent Events) Client Example

This demonstrates how to use SSE as a fallback when WebSocket is blocked.
SSE works over HTTP and is compatible with corporate firewalls.

Run this example:
1. Start server: python examples/sse_streaming_server.py
2. Run client: python examples/sse_client.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
import json
from datetime import datetime


class SSEClient:
    """Simple SSE client for agent streaming."""
    
    def __init__(self, url: str = "http://localhost:8001/sse/python-client"):
        self.url = url
    
    async def connect_and_listen(self):
        """Connect to SSE endpoint and listen for events."""
        print(f"🔌 Connecting to {self.url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status != 200:
                    print(f"❌ Connection failed: {response.status}")
                    return
                
                print("✅ Connected via SSE!\n")
                
                # Read SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line:
                        continue
                    
                    # Parse SSE format
                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                    elif line.startswith('data:'):
                        data_str = line.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            await self.handle_event(event_type if 'event_type' in locals() else 'message', data)
                        except json.JSONDecodeError:
                            pass
    
    async def handle_event(self, event_type: str, data: dict):
        """Handle incoming event."""
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        try:
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%H:%M:%S")
        except:
            time_str = "??:??:??"
        
        # Handle different event types
        if event_type == "connection":
            print(f"[{time_str}] 🔗 {data.get('status', 'connected').upper()}")
            print(f"           ID: {data.get('connection_id')}")
            print(f"           Subscribed to: {data.get('subscribed_to', 'all')}\n")
        
        elif event_type == "agent_start":
            print(f"[{time_str}] 🤖 AGENT START: {data.get('agent_name')}")
            print(f"           Task: {data.get('task')}")
            print(f"           Max steps: {data.get('max_steps')}\n")
        
        elif event_type == "thought":
            print(f"[{time_str}] 💭 THOUGHT (step {data.get('step_index', '?')})")
            print(f"           {data.get('thought')}\n")
        
        elif event_type == "tool_call_start":
            print(f"[{time_str}] 🔧 TOOL CALL: {data.get('tool_name')}")
            args = data.get('arguments', {})
            print(f"           Args: {json.dumps(args)}\n")
        
        elif event_type == "tool_call_end":
            success = "✅" if data.get('success') else "❌"
            print(f"[{time_str}] {success} TOOL RESULT: {data.get('tool_name')}")
            print(f"           Result: {data.get('result')}\n")
        
        elif event_type == "response_chunk":
            chunk = data.get('chunk', '')
            print(f"{chunk}", end='', flush=True)
            if data.get('is_final'):
                print()
        
        elif event_type == "agent_end":
            print(f"\n[{time_str}] 🏁 AGENT COMPLETE")
            print(f"           Result: {data.get('result')}")
            print(f"           Steps: {data.get('total_steps')}")
            print(f"           Time: {data.get('execution_time'):.2f}s\n")
            print("=" * 60 + "\n")
        
        elif event_type == "ping":
            print(f"[{time_str}] 🏓 Keepalive ping")
        
        else:
            print(f"[{time_str}] ❓ {event_type}: {json.dumps(data)}\n")


async def main():
    """Main client function."""
    print("=" * 60)
    print("🔄 CRAFT SSE Stream Client")
    print("=" * 60)
    print("\n📡 Listening for agent events via SSE...")
    print("💡 SSE works even when WebSocket is blocked!\n")
    
    client = SSEClient()
    
    try:
        await client.connect_and_listen()
    except KeyboardInterrupt:
        print("\n👋 Client stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the SSE server is running:")
        print("   python examples/sse_streaming_server.py")
        print("\nOr try WebSocket instead:")
        print("   python examples/websocket_client.py")


if __name__ == "__main__":
    asyncio.run(main())
