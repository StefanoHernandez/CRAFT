"""Server-Sent Events (SSE) streaming endpoint.

SSE provides a fallback mechanism for environments where WebSocket
connections are blocked (corporate firewalls, proxies, etc.).

SSE is unidirectional (server → client) but simpler and more reliable
in restricted networks.
"""

from typing import Optional, AsyncGenerator
import asyncio
import json
import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from craft.api.events import (
    EventEmitter,
    AgentEvent,
    get_global_emitter
)


logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """
    Manages SSE connections for agent streaming.
    
    Similar to WebSocket ConnectionManager but for SSE.
    """
    
    def __init__(self):
        self.active_connections: dict[str, asyncio.Queue] = {}
        self.subscriptions: dict[str, Optional[str]] = {}
    
    def connect(self, connection_id: str, agent_name: Optional[str] = None) -> asyncio.Queue:
        """
        Register SSE connection.
        
        Args:
            connection_id: Unique connection identifier
            agent_name: Optional agent filter
        
        Returns:
            Event queue for this connection
        """
        queue = asyncio.Queue()
        self.active_connections[connection_id] = queue
        self.subscriptions[connection_id] = agent_name
        
        logger.info(f"SSE client {connection_id} connected (agent: {agent_name or 'all'})")
        
        return queue
    
    def disconnect(self, connection_id: str) -> None:
        """Remove connection."""
        self.active_connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        logger.info(f"SSE client {connection_id} disconnected")
    
    async def broadcast_event(self, event: AgentEvent) -> None:
        """
        Broadcast event to subscribed SSE connections.
        
        Args:
            event: Event to broadcast
        """
        # Convert event to dict
        event_dict = event.model_dump(mode='json')
        event_dict["event_type"] = event.event_type.value
        
        # Send to matching subscriptions
        for connection_id, agent_name in self.subscriptions.items():
            if agent_name is None or agent_name == event.agent_name:
                queue = self.active_connections.get(connection_id)
                if queue:
                    try:
                        await queue.put(event_dict)
                    except Exception as e:
                        logger.error(f"Error queueing event for {connection_id}: {e}")


# Global SSE manager
sse_manager = SSEConnectionManager()


async def event_generator(
    connection_id: str,
    agent_name: Optional[str] = None,
    emitter: Optional[EventEmitter] = None
) -> AsyncGenerator[dict, None]:
    """
    Generate SSE events for a connection.
    
    Args:
        connection_id: Connection identifier
        agent_name: Optional agent filter
        emitter: Event emitter to use
    
    Yields:
        Event dictionaries for SSE
    """
    event_emitter = emitter or get_global_emitter()
    
    # Register connection
    queue = sse_manager.connect(connection_id, agent_name)
    
    try:
        # Send connection event
        yield {
            "event": "connection",
            "data": json.dumps({
                "status": "connected",
                "connection_id": connection_id,
                "subscribed_to": agent_name or "all",
                "timestamp": datetime.now().isoformat()
            })
        }
        
        # Stream events from queue
        while True:
            try:
                # Wait for next event with timeout
                event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                yield {
                    "event": event_data.get("event_type", "message"),
                    "data": json.dumps(event_data)
                }
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield {
                    "event": "ping",
                    "data": json.dumps({
                        "timestamp": datetime.now().isoformat()
                    })
                }
                
    except asyncio.CancelledError:
        logger.info(f"SSE connection {connection_id} cancelled")
    
    finally:
        # Cleanup
        sse_manager.disconnect(connection_id)


def add_sse_endpoints(app: FastAPI, emitter: Optional[EventEmitter] = None):
    """
    Add SSE endpoints to FastAPI app.
    
    Args:
        app: FastAPI application
        emitter: Event emitter to use
    
    Example:
        from fastapi import FastAPI
        from craft.api.sse import add_sse_endpoints
        
        app = FastAPI()
        add_sse_endpoints(app)
    """
    
    @app.get("/sse/{connection_id}")
    async def sse_endpoint(
        connection_id: str,
        agent_name: Optional[str] = None
    ):
        """
        Server-Sent Events endpoint for agent streaming.
        
        This endpoint provides an HTTP-based alternative to WebSocket
        for streaming agent events. Use this in environments where
        WebSocket connections are blocked.
        
        Args:
            connection_id: Unique client identifier
            agent_name: Optional agent name filter
        
        Returns:
            EventSource stream
        
        Usage:
            // JavaScript client
            const eventSource = new EventSource(
                'http://localhost:8000/sse/client123?agent_name=my_agent'
            );
            
            eventSource.addEventListener('thought', (event) => {
                const data = JSON.parse(event.data);
                console.log('Thought:', data.thought);
            });
            
            eventSource.addEventListener('tool_call_start', (event) => {
                const data = JSON.parse(event.data);
                console.log('Tool call:', data.tool_name);
            });
            
            eventSource.onmessage = (event) => {
                console.log('Event:', event);
            };
        """
        return EventSourceResponse(
            event_generator(connection_id, agent_name, emitter)
        )
    
    @app.get("/sse/stats")
    async def sse_stats():
        """Get SSE connection statistics."""
        return {
            "total_connections": len(sse_manager.active_connections),
            "active_connections": list(sse_manager.active_connections.keys()),
            "subscriptions": {
                conn_id: agent_name or "all"
                for conn_id, agent_name in sse_manager.subscriptions.items()
            }
        }


async def broadcast_to_sse(emitter: EventEmitter):
    """
    Background task to broadcast events to SSE clients.
    
    Args:
        emitter: Event emitter to listen to
    """
    # Create a queue for this listener
    queue = asyncio.Queue()
    emitter.add_listener(queue)
    
    try:
        while True:
            # Get next event
            event = await queue.get()
            
            # Broadcast to SSE clients
            await sse_manager.broadcast_event(event)
            
    finally:
        emitter.remove_listener(queue)


def create_sse_app(emitter: Optional[EventEmitter] = None) -> FastAPI:
    """
    Create FastAPI app with SSE endpoints.
    
    Args:
        emitter: Event emitter to use
    
    Returns:
        FastAPI application with SSE support
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="CRAFT SSE Streaming API",
        description="Server-Sent Events API for agent streaming (WebSocket fallback)",
        version="1.0.0"
    )
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add SSE endpoints
    add_sse_endpoints(app, emitter)
    
    event_emitter = emitter or get_global_emitter()
    
    @app.on_event("startup")
    async def startup_event():
        """Start SSE broadcaster on startup."""
        asyncio.create_task(broadcast_to_sse(event_emitter))
        logger.info("SSE streaming API started")
    
    @app.get("/")
    async def root():
        """API info."""
        return {
            "name": "CRAFT SSE Streaming API",
            "version": "1.0.0",
            "sse_url": "/sse/{connection_id}",
            "stats_url": "/sse/stats",
            "note": "Server-Sent Events fallback for WebSocket"
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=logging.INFO)
    
    app = create_sse_app()
    
    print("=" * 60)
    print("🔄 CRAFT SSE Streaming Server")
    print("=" * 60)
    print("\n📍 Server starting on: http://localhost:8001")
    print("📡 SSE endpoint: http://localhost:8001/sse/{connection_id}")
    print("\n💡 Use SSE when WebSocket is blocked by firewall/proxy")
    print("   Example: http://localhost:8001/sse/my-client?agent_name=demo")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
