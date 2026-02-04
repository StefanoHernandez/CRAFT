from typing import Dict, List, Any
import json

class GraphParser:
    """
    Parses a Stitch visual graph (JSON) and generates executable Python code
    using the CRAFT framework.
    """
    
    def __init__(self, graph_data: Dict[str, Any]):
        self.nodes = graph_data.get("nodes", [])
        self.connections = graph_data.get("connections", [])
        self.agents = []
        self.tools = []
        
    def generate_code(self) -> str:
        """Main entry point to generate the full Python script."""
        self._parse_nodes()
        
        script = self._generate_imports()
        script += self._generate_tools()
        script += self._generate_agents()
        script += self._generate_main_flow()
        
        return script
        
    def _parse_nodes(self):
        """Separate nodes by type."""
        for node in self.nodes:
            if node.get("type") == "agent":
                self.agents.append(node)
            elif node.get("type") == "tool":
                self.tools.append(node)
                
    def _generate_imports(self) -> str:
        return """import asyncio
from craft.agents import Agent
from craft.providers import OpenAIProvider, AnthropicProvider
from craft.tools import Tool
from craft.consensus import Council, CouncilConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize default provider
provider = OpenAIProvider()
"""

    def _generate_tools(self) -> str:
        code = "\n# --- Tools ---\n"
        for tool in self.tools:
            name = tool.get("name", "tool").lower().replace(" ", "_")
            # For now, we generate a mock tool or looking for standard tools
            # In a real implementation, we might parse the 'data' field for function logic
            code += f"""
def {name}_func(arg1: str) -> str:
    \"\"\"Mock implementation for {tool.get('name')}.\"\"\"
    return f"Processed {{arg1}} with {name}"

{name} = Tool(
    name="{name}",
    description="Auto-generated tool for {tool.get('name')}",
    func={name}_func
)
"""
        return code

    def _generate_agents(self) -> str:
        code = "\n# --- Agents ---\n"
        for agent in self.agents:
            name = agent.get("name", "Agent").lower().replace(" ", "_")
            role = agent.get("data", {}).get("role", "Assistant")
            goal = agent.get("data", {}).get("goal", "Help the user")
            
            # Find tools connected to this agent
            agent_tools = []
            agent_id = agent.get("id")
            for conn in self.connections:
                if conn.get("to") == agent_id:
                    from_id = conn.get("from")
                    # Check if 'from' is a tool
                    tool_node = next((t for t in self.tools if t["id"] == from_id), None)
                    if tool_node:
                        tool_name = tool_node.get("name", "tool").lower().replace(" ", "_")
                        agent_tools.append(tool_name)
                        
            tools_str = f"[{', '.join(agent_tools)}]" if agent_tools else "[]"
            
            code += f"""
{name} = Agent(
    name="{agent.get('name')}",
    role="{role}",
    goal="{goal}",
    provider=provider,
    tools={tools_str}
)
"""
        return code

    def _generate_main_flow(self) -> str:
        # Simple execution flow: run all agents or the first one
        if not self.agents:
            return "\n# No agents defined to run.\n"
            
        main_agent_var = self.agents[0].get("name", "Agent").lower().replace(" ", "_")
        
        return f"""
async def main():
    print("🚀 Starting Agent Execution...")
    
    # Example execution for {main_agent_var}
    response = await {main_agent_var}.arun("Make a plan for this project")
    print(f"Result: {{response.result}}")

if __name__ == "__main__":
    asyncio.run(main())
"""
