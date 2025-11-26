# WebSocket Streaming API - Quick Start

## Overview

CRAFT's WebSocket Streaming API enables **real-time monitoring** of agent execution. Stream agent thoughts, tool calls, and responses as they happen - perfect for building interactive UIs and debugging agents.

**NEW**: SSE (Server-Sent Events) fallback for firewall-restricted environments!

## Why WebSocket Streaming?

✅ **Real-time updates** - See agent reasoning as it happens  
✅ **Better UX** - Build responsive chat interfaces  
✅ **Debugging** - Monitor agent execution step-by-step  
✅ **Multi-client** - Multiple clients can watch the same agent  
✅ **Production-ready** - Built on FastAPI + websockets  
✅ **SSE fallback** - Works even when WebSocket is blocked

## Quick Start

### Option 1: WebSocket (Recommended)

Best for: Real-time bidirectional communication

```python
from craft.api.websocket import run_server

# Start server on port 8000
run_server(port=8000)
```

Or use the example:
```bash
python examples/websocket_streaming_server.py
```

### 2. Connect a Client

**Python Client:**
```bash
python examples/websocket_client.py
```

**JavaScript/Browser Client:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/my-client-id');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Event: ${data.event_type}`, data);
    
    if (data.event_type === 'thought') {
        console.log(`💭 ${data.thought}`);
    } else if (data.event_type === 'tool_call_start') {
        console.log(`🔧 Calling ${data.tool_name}`);
    }
};
```

### Option 2: SSE - Server-Sent Events (Fallback)

Best for: Corporate firewalls, restricted networks

**Python Server:**
```bash
python examples/sse_streaming_server.py
```

**Python Client:**
```bash
python examples/sse_client.py
```

**JavaScript/Browser Client:**
```javascript
const eventSource = new EventSource('http://localhost:8001/sse/my-client-id');

eventSource.addEventListener('thought', (event) => {
    const data = JSON.parse(event.data);
    console.log(`💭 ${data.thought}`);
});

eventSource.addEventListener('tool_call_start', (event) => {
    const data = JSON.parse(event.data);
    console.log(`🔧 ${data.tool_name}`);
});

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
};
```

**When to use SSE:**
- ✅ WebSocket is blocked by firewall/proxy
- ✅ One-way communication (server → client) is sufficient
- ✅ Simpler deployment (just HTTP)
- ✅ Native browser support with EventSource API

### 3. Emit Events from Your Agent
```

### 3. Emit Events from Your Agent

```python
from craft.api.events import (
    emit_agent_start,
    emit_thought,
    emit_tool_call_start,
    emit_agent_end
)

# During agent execution
await emit_agent_start("my_agent", "Solve a problem", max_steps=10)
await emit_thought("my_agent", "I need to search for information")
await emit_tool_call_start("my_agent", "google_search", {"query": "..."})
await emit_agent_end("my_agent", result="Done!", total_steps=3, execution_time=2.5)
```

## Event Types

| Event Type | Description | Data |
|------------|-------------|------|
| `agent_start` | Agent begins execution | `task`, `max_steps` |
| `agent_end` | Agent completes | `result`, `total_steps`, `execution_time` |
| `thought` | Agent reasoning | `thought` |
| `tool_call_start` | Tool execution begins | `tool_name`, `arguments` |
| `tool_call_end` | Tool execution completes | `tool_name`, `result`, `success` |
| `response_chunk` | Streaming response | `chunk`, `is_final` |
| `plan_created` | Planning completed | `plan_steps` |

## API Endpoints

### WebSocket
- **URL**: `ws://localhost:8000/ws/{connection_id}`
- **Query Params**:
  - `agent_name` (optional): Filter events for specific agent

### SSE (Fallback)
- **URL**: `http://localhost:8001/sse/{connection_id}`
- **Query Params**:
  - `agent_name` (optional): Filter events for specific agent
- **Stats**: `GET /sse/stats`

### HTTP
- `GET /` - API info
- `GET /stats` - Connection statistics (WebSocket)
- `GET /health` - Health check

## Advanced Usage

### Subscribe to Specific Agent

```javascript
// Only receive events from "support-agent"
const ws = new WebSocket('ws://localhost:8000/ws/client123?agent_name=support-agent');
```

### Connection Management

```python
from craft.api.websocket import manager

# Get stats
stats = manager.get_stats()
print(f"Active connections: {stats['total_connections']}")

# Broadcast custom event
await manager.broadcast_event(my_event)
```

### Custom Event Emitter

```python
from craft.api.events import EventEmitter
from craft.api.websocket import create_websocket_app

# Create custom emitter
emitter = EventEmitter()

# Create app with custom emitter
app = create_websocket_app(emitter=emitter)

# Emit events
await emitter.emit(my_event)
```

## Integration with Agent Class

**Future enhancement** - The Agent class will automatically emit events:

```python
from craft.agents import Agent

agent = Agent(
    name="my_agent",
    provider=provider,
    enable_streaming=True  # Auto-emit events
)

# Events are automatically emitted during execution
result = await agent.arun("task")
```

## Production Deployment

### CORS Configuration

```python
app = create_websocket_app(enable_cors=True)

# Or customize CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication

Add authentication to WebSocket endpoint:

```python
from fastapi import WebSocket, Depends, HTTPException

async def verify_token(token: str):
    if token != "secret":
        raise HTTPException(status_code=401)
    return token

@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_id: str,
    token: str = Depends(verify_token)
):
    # ... connection handling
```

### Scaling

For multiple server instances, use Redis pub/sub:

```python
import aioredis

redis = aioredis.from_url("redis://localhost")

async def broadcast_via_redis(event):
    await redis.publish("agent_events", event.json())

# Subscribe in each server instance
pubsub = redis.pubsub()
await pubsub.subscribe("agent_events")
```

## Examples

See `examples/` directory:
- `websocket_streaming_server.py` - Demo server with simulated agent
- `websocket_client.py` - Python client example

## Troubleshooting

**Connection refused?**
- Ensure server is running: `python examples/websocket_streaming_server.py`
- Check port: default is 8000

**No events received?**
- Verify events are being emitted: check server logs
- Check subscription filter (`agent_name` parameter)

**Connection drops?**
- Implement ping/pong (see client example)
- Check firewall/proxy settings

## Next Steps

- ✅ Basic WebSocket streaming working
- ✅ **SSE fallback (DONE!)** - for firewalls that block WebSocket
- 🚧 React hooks (`useAgentStream`, `useAgentState`)
- 🚧 Auto-integration with Agent class
- 🚧 Event replay/history API

## Support

Issues? Check:
- [FastAPI WebSocket docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [websockets library](https://websockets.readthedocs.io/)
- CRAFT GitHub issues

---

**⚡ This is a CRAFT exclusive feature!** No other framework (LangChain, CrewAI, AutoGen) has built-in WebSocket streaming.
