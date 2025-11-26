"""
WebSocket Client Example for CRAFT Agent Streaming

This client connects to the CRAFT WebSocket server and displays
real-time agent execution events.

Prerequisites:
1. Start server: python examples/websocket_streaming_server.py

Then run this client:
    python examples/websocket_client.py
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime


class AgentStreamClient:
    """Simple WebSocket client for agent streaming."""
    
    def __init__(self, url: str = "ws://localhost:8000/ws/python-client"):
        self.url = url
        self.websocket = None
    
    async def connect(self):
        """Connect to WebSocket server."""
        print(f"🔌 Connecting to {self.url}...")
        self.websocket = await websockets.connect(self.url)
        print("✅ Connected!\n")
    
    async def listen(self):
        """Listen for events from server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_event(data)
        
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Connection closed")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    async def handle_event(self, event: dict):
        """
        Handle incoming event.
        
        Args:
            event: Event data from server
        """
        event_type = event.get("event_type", event.get("type"))
        timestamp = event.get("timestamp", datetime.now().isoformat())
        
        # Format time
        try:
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%H:%M:%S")
        except:
            time_str = "??:??:??"
        
        # Handle different event types
        if event_type == "connection":
            print(f"[{time_str}] 🔗 {event.get('status', 'connected').upper()}")
            print(f"           ID: {event.get('connection_id')}")
            print(f"           Subscribed to: {event.get('subscribed_to', 'all')}\n")
        
        elif event_type == "agent_start":
            print(f"[{time_str}] 🤖 AGENT START: {event.get('agent_name')}")
            print(f"           Task: {event.get('task')}")
            print(f"           Max steps: {event.get('max_steps')}\n")
        
        elif event_type == "thought":
            print(f"[{time_str}] 💭 THOUGHT (step {event.get('step_index', '?')})")
            print(f"           {event.get('thought')}\n")
        
        elif event_type == "tool_call_start":
            print(f"[{time_str}] 🔧 TOOL CALL: {event.get('tool_name')}")
            args = event.get('arguments', {})
            print(f"           Args: {json.dumps(args, indent=11)}\n")
        
        elif event_type == "tool_call_end":
            success = "✅" if event.get('success') else "❌"
            print(f"[{time_str}] {success} TOOL RESULT: {event.get('tool_name')}")
            print(f"           Result: {event.get('result')}\n")
        
        elif event_type == "response_chunk":
            chunk = event.get('chunk', '')
            is_final = "🏁" if event.get('is_final') else ""
            print(f"{chunk}", end='', flush=True)
            if is_final:
                print()  # Newline after final chunk
        
        elif event_type == "agent_end":
            print(f"\n[{time_str}] 🏁 AGENT COMPLETE")
            print(f"           Result: {event.get('result')}")
            print(f"           Steps: {event.get('total_steps')}")
            print(f"           Time: {event.get('execution_time'):.2f}s\n")
            print("=" * 60 + "\n")
        
        elif event_type == "pong":
            print(f"[{time_str}] 🏓 Pong received")
        
        else:
            # Unknown event type
            print(f"[{time_str}] ❓ {event_type}: {json.dumps(event, indent=2)}\n")
    
    async def send_ping(self):
        """Send ping to keep connection alive."""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "ping"}))
    
    async def run(self):
        """Run client."""
        await self.connect() 
      
        # Create ping task
        async def ping_loop():
            while True:
                await asyncio.sleep(30)
                await self.send_ping()
        
        ping_task = asyncio.create_task(ping_loop())
        
        try:
            await self.listen()
        finally:
            ping_task.cancel()
            if self.websocket:
                await self.websocket.close()


async def main():
    """Main client function."""
    print("=" * 60)
    print("🎧 CRAFT WebSocket Stream Client")
    print("=" * 60)
    print("\n📡 Listening for agent events...\n")
    
    client = AgentStreamClient()
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Client stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the server is running:")
        print("   python examples/websocket_streaming_server.py")


if __name__ == "__main__":
    asyncio.run(main())
