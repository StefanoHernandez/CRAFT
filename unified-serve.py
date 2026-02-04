import os
import asyncio
import logging
import random
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from craft.api.websocket import manager, broadcast_agent_events
from craft.api.events import get_global_emitter, emit_agent_start, emit_thought, emit_tool_call_start, emit_tool_call_end, emit_agent_end

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.hub")

app = FastAPI(title="CRAFT Nexus Integrated Hub")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket statistics endpoint
@app.get("/stats")
async def get_stats():
    return manager.get_stats()

# Code Export Endpoint
@app.post("/api/export")
async def export_workflow_code(workflow: dict):
    from stitch.graph_parser import GraphParser
    try:
        parser = GraphParser(workflow)
        code = parser.generate_code()
        return {"success": True, "code": code}
    except Exception as e:
        logger.error(f"Error exporting code: {e}")
        return {"success": False, "error": str(e)}

        return {"success": False, "error": str(e)}

# Partial Execution Endpoint
@app.post("/api/run_node")
async def run_single_node(payload: dict):
    from craft.agents import Agent
    from craft.providers import OpenAIProvider
    try:
        node = payload.get("node")
        user_input = payload.get("input", "")
        
        if not node:
            raise ValueError("No node data provided")
            
        if node.get("type") == "agent":
            # Instantiate a temporary agent
            # In a real app, strict DI and caching would be used
            agent_name = node.get("name", "TempAgent")
            role = node.get("data", {}).get("role", "Assistant")
            goal = node.get("data", {}).get("goal", "Help the user")
            
            # Use OpenAI by default for now
            provider = OpenAIProvider()
            
            agent = Agent(
                name=agent_name,
                role=role,
                goal=goal,
                provider=provider
            )
            
            # Execute
            result = await agent.arun(user_input)
            return {"success": True, "output": result.result}
            
        elif node.get("type") == "tool":
            return {"success": True, "output": f"Tool execution for '{node.get('name')}' mock successful with input: {user_input}"}
            
        else:
            return {"success": False, "error": f"Unknown node type: {node.get('type')}"}
            
    except Exception as e:
        logger.error(f"Error running node: {e}")
        return {"success": False, "error": str(e)}

# Partial Execution Endpoint
@app.post("/api/run_node")
async def run_single_node(payload: dict):
    from craft.agents import Agent
    from craft.providers import OpenAIProvider
    try:
        node = payload.get("node")
        user_input = payload.get("input", "")
        
        if not node:
            raise ValueError("No node data provided")
            
        if node.get("type") == "agent":
            # Instantiate a temporary agent
            # In a real app, strict DI and caching would be used
            agent_name = node.get("name", "TempAgent")
            role = node.get("data", {}).get("role", "Assistant")
            goal = node.get("data", {}).get("goal", "Help the user")
            
            # Use OpenAI by default for now
            provider = OpenAIProvider()
            
            agent = Agent(
                name=agent_name,
                role=role,
                goal=goal,
                provider=provider
            )
            
            # Execute
            result = await agent.arun(user_input)
            return {"success": True, "output": result.result}
            
        elif node.get("type") == "tool":
            return {"success": True, "output": f"Tool execution for '{node.get('name')}' mock successful with input: {user_input}"}
            
        else:
            return {"success": False, "error": f"Unknown node type: {node.get('type')}"}
            
    except Exception as e:
        logger.error(f"Error running node: {e}")
        return {"success": False, "error": str(e)}

WORKFLOWS_FILE = "stitch/workflows.json"

def save_workflow(data):
    import json
    try:
        with open(WORKFLOWS_FILE, "w") as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving workflow: {e}")
        return False

# WebSocket endpoint
@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    await manager.connect(websocket, connection_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, connection_id)
            elif data.get("type") == "save_workflow":
                success = save_workflow(data.get("data"))
                await manager.send_personal_message({
                    "type": "save_status",
                    "success": success,
                    "message": "Workflow saved successfully" if success else "Error saving workflow"
                }, connection_id)
            elif data.get("type") == "run_workflow":
                # Start a simulated execution loop for the nodes
                nodes = data.get("data", {}).get("nodes", [])
                asyncio.create_task(simulate_workflow_execution(nodes, connection_id))
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)

async def simulate_workflow_execution(nodes, connection_id):
    """Simulates node-by-node execution for visual feedback."""
    for node in nodes:
        # 1. Update node status to 'executing'
        await manager.send_personal_message({
            "type": "node_status",
            "node_id": node['id'],
            "status": "executing"
        }, connection_id)
        
        # 2. Simulate work
        await asyncio.sleep(2)
        
        # 3. Update node status to 'completed'
        await manager.send_personal_message({
            "type": "node_status",
            "node_id": node['id'],
            "status": "completed"
        }, connection_id)
        
        # 4. Emit a thought for the terminal
        emitter = get_global_emitter()
        await emit_thought("nexus_worker", f"Processed node {node['name']} ({node['id']}) successfully.")

# Background task to emit random metrics and simulated agent events
async def background_simulator():
    emitter = get_global_emitter()
    agent_name = "nexus_orchestrator"
    
    while True:
        # 1. Emit simulated metrics
        metrics = {
            "type": "metrics",
            "data": {
                "tokens_per_sec": random.randint(45, 120),
                "active_tools": random.randint(2, 5),
                "cost": round(random.uniform(0.12, 0.45), 2),
                "memory": random.randint(15, 40),
                "cpu": random.randint(5, 25)
            }
        }
        # Broadcast via manager to all connected clients
        for conn_id in manager.active_connections:
            await manager.send_personal_message(metrics, conn_id)
            
        # 3. Occasionally simulate an agent thought
        if random.random() > 0.7:
            thoughts = [
                "Analyzing system load for optimal agent distribution...",
                "Optimizing RAG vector search parameters...",
                "Scaling worker nodes in district-core...",
                "Validating tool execution timeouts...",
                "Synchronizing global configuration with provider nodes...",
                "Running heuristic evaluation on agent memory usage..."
            ]
            await emit_thought(agent_name, random.choice(thoughts))
            
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup():
    # Start event broadcaster
    emitter = get_global_emitter()
    asyncio.create_task(broadcast_agent_events(emitter))
    # Start background simulator
    asyncio.create_task(background_simulator())
    logger.info("🚀 CRAFT Nexus Integrated Server Ready")

# Mount static files AFTER routes
# This serves everything in the current directory (stitch/)
app.mount("/", StaticFiles(directory="stitch", html=True), name="static")

if __name__ == "__main__":
    # In a real app, you would use 'uvicorn serve:app'
    uvicorn.run(app, host="0.0.0.0", port=8000)
