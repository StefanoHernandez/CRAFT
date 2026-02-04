import logging
import asyncio
from craft.agents import Agent
from craft.providers import OpenAIProvider
from craft.api.schemas import NodeData
from craft.api.websocket import manager
from craft.api.events import get_global_emitter, emit_thought

logger = logging.getLogger("nexus.execution")

class ExecutionService:
    @staticmethod
    async def run_single_node(node: NodeData, user_input: str = "") -> dict:
        """Execute a single node (Agent or Tool) and return the result."""
        try:
            if node.type == "agent":
                # Instantiate a temporary agent
                # In a real app, strict DI and caching would be used
                agent_name = node.name or "TempAgent"
                role = node.data.get("role", "Assistant")
                goal = node.data.get("goal", "Help the user")
                
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
                return {"success": True, "output": result.text} # using result.text as per verification
                
            elif node.type == "tool":
                # Mock tool execution for now
                return {"success": True, "output": f"Tool execution for '{node.name}' mock successful with input: {user_input}"}
                
            else:
                return {"success": False, "error": f"Unknown node type: {node.type}"}
                
        except Exception as e:
            logger.error(f"Error running node {node.id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def simulate_workflow_execution(nodes: list, connection_id: str):
        """Simulates node-by-node execution for visual feedback."""
        for node in nodes:
            node_id = node.get('id')
            node_name = node.get('name')
            
            # 1. Update node status to 'executing'
            await manager.send_personal_message({
                "type": "node_status",
                "node_id": node_id,
                "status": "executing"
            }, connection_id)
            
            # 2. Simulate work
            await asyncio.sleep(2)
            
            # 3. Update node status to 'completed'
            await manager.send_personal_message({
                "type": "node_status",
                "node_id": node_id,
                "status": "completed"
            }, connection_id)
            
            # 4. Emit a thought for the terminal
            # emitter = get_global_emitter() # Emitter is global
            await emit_thought("nexus_worker", f"Processed node {node_name} ({node_id}) successfully.")
