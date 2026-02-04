"""WebSocket server for real-time agent streaming.

Provides WebSocket endpoints for streaming agent execution events in real-time.
Clients can connect and receive live updates as agents reason, call tools, and respond.
"""

from typing import Dict, Set, Optional, Any
import asyncio
import json
import logging
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from craft.api.events import (
    EventEmitter,
    AgentEvent,
    get_global_emitter
)
from craft.agents.agent import Agent


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for agent streaming.
    
    Handles multiple concurrent connections, broadcasts events,
    and tracks connection lifecycle.
    """
    
    def __init__(self):
        # Active connections: {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection subscriptions: {connection_id: agent_name or None for all}
        self.subscriptions: Dict[str, Optional[str]] = {}
        
        # Event queues for each connection
        self.event_queues: Dict[str, asyncio.Queue] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        agent_name: Optional[str] = None
    ) -> None:
        """
        Accept and register WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            agent_name: Optional agent name to subscribe to (None = all agents)
        """
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = agent_name
        self.event_queues[connection_id] = asyncio.Queue()
        
        logger.info(f"Client {connection_id} connected (agent: {agent_name or 'all'})")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "subscribed_to": agent_name or "all",
            "timestamp": datetime.now().isoformat()
        }, connection_id)
    
    def disconnect(self, connection_id: str) -> None:
        """
        Remove connection.
        
        Args:
            connection_id: Connection to remove
        """
        self.active_connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        self.event_queues.pop(connection_id, None)
        
        logger.info(f"Client {connection_id} disconnected")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> None:
        """
        Send message to specific connection.
        
        Args:
            message: Message to send
            connection_id: Target connection
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_event(self, event: AgentEvent) -> None:
        """
        Broadcast event to subscribed connections.
        
        Args:
            event: Event to broadcast
        """
        # Convert event to dict
        event_dict = event.model_dump(mode='json')
        event_dict["event_type"] = event.event_type.value
        
        # Send to matching subscriptions via queues
        for connection_id, agent_name in self.subscriptions.items():
            # Check if this connection should receive the event
            if agent_name is None or agent_name == event.agent_name:
                queue = self.event_queues.get(connection_id)
                if queue:
                    try:
                        # Non-blocking put to ensure broadcaster is never blocked by a slow client
                        queue.put_nowait(event_dict)
                    except asyncio.QueueFull:
                        logger.warning(f"Event queue full for client {connection_id}, dropping event")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "active_connections": list(self.active_connections.keys()),
            "subscriptions": {
                conn_id: agent_name or "all"
                for conn_id, agent_name in self.subscriptions.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


def create_websocket_app(
    emitter: Optional[EventEmitter] = None,
    enable_cors: bool = True
) -> FastAPI:
    """
    Create FastAPI app with WebSocket endpoints.
    
    Args:
        emitter: Event emitter to use (default: global emitter)
        enable_cors: Whether to enable CORS middleware
    
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="CRAFT Agent Streaming API",
        description="WebSocket API for real-time agent execution streaming",
        version="1.0.0"
    )
    
    # Enable CORS for web clients
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    event_emitter = emitter or get_global_emitter()
    
    @app.get("/")
    async def root():
        """API info endpoint."""
        return {
            "name": "CRAFT Agent Streaming API",
            "version": "1.0.0",
            "websocket_url": "/ws/{connection_id}",
            "stats_url": "/stats"
        }
    
    @app.get("/stats")
    async def get_stats():
        """Get connection statistics."""
        return manager.get_stats()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "connections": len(manager.active_connections)
        }
    
    @app.websocket("/ws/{connection_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        connection_id: str,
        agent_name: Optional[str] = None
    ):
        """
        WebSocket endpoint for agent event streaming.
        
        Args:
            websocket: WebSocket connection
            connection_id: Unique client identifier
            agent_name: Optional agent name to filter events (None = all agents)
        
        Usage:
            # JavaScript client
            const ws = new WebSocket('ws://localhost:8000/ws/client123?agent_name=my_agent');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Event:', data.event_type, data);
            };
        """
        await manager.connect(websocket, connection_id, agent_name)
        
        try:
            # Create event sender task
            async def sender_task():
                """Send events from queue to websocket."""
                queue = manager.event_queues[connection_id]
                try:
                    while True:
                        # Get message from queue
                        message = await queue.get()
                        
                        # Send to websocket
                        await websocket.send_json(message)
                        
                        # Mark task as done
                        queue.task_done()
                except asyncio.CancelledError:
                    # Task cancelled, normal shutdown
                    pass
                except Exception as e:
                    logger.error(f"Sender task error for {connection_id}: {e}")
            
            # Start sender
            sender = asyncio.create_task(sender_task())
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Receive messages (e.g., ping, configuration changes)
                    data = await websocket.receive_json()
                    
                    # Handle different message types
                    if data.get("type") == "ping":
                        await manager.send_personal_message({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }, connection_id)
                    
                    elif data.get("type") == "subscribe":
                        # Update subscription
                        new_agent = data.get("agent_name")
                        manager.subscriptions[connection_id] = new_agent
                        await manager.send_personal_message({
                            "type": "subscription_updated",
                            "agent_name": new_agent or "all"
                        }, connection_id)
                
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
            
            # Cleanup
            sender.cancel()
            try:
                await sender
            except asyncio.CancelledError:
                pass
            
        finally:
            manager.disconnect(connection_id)
    
    return app


async def broadcast_agent_events(emitter: EventEmitter):
    """
    Background task to broadcast agent events to WebSocket clients.
    
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
            
            # Broadcast to WebSocket clients
            await manager.broadcast_event(event)
            
    finally:
        emitter.remove_listener(queue)


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    emitter: Optional[EventEmitter] = None
):
    """
    Run WebSocket server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        emitter: Event emitter to use
    
    Example:
        from craft.api.websocket import run_server
        from craft.api.events import get_global_emitter
        
        # Run server
        run_server(port=8000)
        
        # In another process/thread, execute agent:
        agent = Agent(...)
        result = await agent.arun("task")
        # Events will be streamed to connected WebSocket clients!
    """
    import uvicorn
    
    app = create_websocket_app(emitter)
    
    # Start event broadcaster
    event_emitter = emitter or get_global_emitter()
    
    @app.on_event("startup")
    async def startup_event():
        """Start event broadcaster on startup."""
        asyncio.create_task(broadcast_agent_events(event_emitter))
        logger.info(f"WebSocket server starting on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Example: Run server
    logging.basicConfig(level=logging.INFO)
    run_server(port=8000)
