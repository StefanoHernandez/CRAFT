import logging
import uvicorn
import asyncio
import random
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect

from craft.api.server import create_app
from craft.api.schemas import RunNodeRequest, ExportWorkflowRequest
from craft.services.execution import ExecutionService
from craft.api.websocket import manager
from craft.api.events import get_global_emitter, emit_thought

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.hub")

app = create_app()

# API Endpoints
@app.get("/stats")
async def get_stats():
    return manager.get_stats()

@app.post("/api/export")
async def export_workflow_code(request: ExportWorkflowRequest):
    from stitch.graph_parser import GraphParser
    try:
        # Compatibility adapter for GraphParser which expects dict
        workflow_dict = request.workflow.model_dump()
        parser = GraphParser(workflow_dict)
        code = parser.generate_code()
        return {"success": True, "code": code}
    except Exception as e:
        logger.error(f"Error exporting code: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/run_node")
async def run_single_node(payload: RunNodeRequest):
    return await ExecutionService.run_single_node(payload.node, payload.input)

# File Persistence (Simplified)
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
                asyncio.create_task(ExecutionService.simulate_workflow_execution(nodes, connection_id))
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)

# Background task to emit random metrics and simulated agent events
async def background_simulator():
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
async def startup_tasks():
    # Additional startup tasks if any (event broadcaster is in lifespan)
    asyncio.create_task(background_simulator())

# Mount static files AFTER routes
app.mount("/", StaticFiles(directory="stitch", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
