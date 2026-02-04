"""
CRAFT Graph Parser - Converts visual workflow graphs to executable Python code.

Inspired by n8n's node-based workflow system, adapted for CRAFT's capabilities.
"""

from typing import Dict, List, Any, Optional, Set
import json


# ============================================================================
# NODE TAXONOMY - All CRAFT capabilities mapped to visual node types
# ============================================================================

NODE_CATEGORIES = {
    "triggers": {
        "user_input": {"icon": "input", "color": "sky"},
        "webhook": {"icon": "webhook", "color": "sky"},
        "schedule": {"icon": "schedule", "color": "sky"},
        "chat_trigger": {"icon": "chat", "color": "sky"},
    },
    "agents": {
        "agent": {"icon": "psychology", "color": "amber"},
        "planning_agent": {"icon": "schema", "color": "amber"},
        "research_agent": {"icon": "search", "color": "amber"},
        "code_review_agent": {"icon": "code", "color": "amber"},
        "content_writer_agent": {"icon": "edit_note", "color": "amber"},
        "data_analyst_agent": {"icon": "analytics", "color": "amber"},
    },
    "consensus": {
        "council": {"icon": "groups", "color": "orange"},
        "debate": {"icon": "forum", "color": "orange"},
        "voting": {"icon": "how_to_vote", "color": "orange"},
        "peer_review": {"icon": "rate_review", "color": "orange"},
        "hierarchical": {"icon": "account_tree", "color": "orange"},
    },
    "providers": {
        "openai": {"icon": "auto_awesome", "color": "emerald"},
        "anthropic": {"icon": "smart_toy", "color": "emerald"},
        "google": {"icon": "cloud", "color": "emerald"},
        "groq": {"icon": "bolt", "color": "emerald"},
        "mistral": {"icon": "air", "color": "emerald"},
        "ollama": {"icon": "computer", "color": "emerald"},
        "azure_openai": {"icon": "cloud_circle", "color": "emerald"},
        "cohere": {"icon": "hub", "color": "emerald"},
    },
    "tools": {
        "web_search": {"icon": "search", "color": "blue"},
        "calculator": {"icon": "calculate", "color": "blue"},
        "http_request": {"icon": "http", "color": "blue"},
        "read_file": {"icon": "folder_open", "color": "blue"},
        "write_file": {"icon": "save", "color": "blue"},
        "database_query": {"icon": "database", "color": "blue"},
        "send_email": {"icon": "email", "color": "blue"},
        "custom_tool": {"icon": "build", "color": "blue"},
    },
    "rag": {
        "document_loader": {"icon": "upload_file", "color": "teal"},
        "pdf_loader": {"icon": "picture_as_pdf", "color": "teal"},
        "text_chunker": {"icon": "content_cut", "color": "teal"},
        "embedding": {"icon": "data_array", "color": "teal"},
        "vector_store": {"icon": "storage", "color": "teal"},
        "vector_search": {"icon": "manage_search", "color": "teal"},
        "hybrid_search": {"icon": "join", "color": "teal"},
        "reranker": {"icon": "sort", "color": "teal"},
        "query_rewriter": {"icon": "edit", "color": "teal"},
    },
    "memory": {
        "conversation_memory": {"icon": "history", "color": "violet"},
        "persistent_memory": {"icon": "save_alt", "color": "violet"},
        "context_manager": {"icon": "layers", "color": "violet"},
    },
    "logic": {
        "condition": {"icon": "call_split", "color": "purple"},
        "loop": {"icon": "loop", "color": "purple"},
        "switch": {"icon": "alt_route", "color": "purple"},
        "merge": {"icon": "merge", "color": "purple"},
        "error_handler": {"icon": "error", "color": "purple"},
    },
    "output": {
        "text_output": {"icon": "text_fields", "color": "slate"},
        "json_output": {"icon": "data_object", "color": "slate"},
        "file_output": {"icon": "file_download", "color": "slate"},
        "webhook_response": {"icon": "send", "color": "slate"},
    }
}


class GraphParser:
    """
    Parses a Stitch visual graph (JSON) and generates executable Python code
    using the CRAFT framework.

    Node types supported:
    - triggers: user_input, webhook, schedule, chat_trigger
    - agents: agent, planning_agent, research_agent, etc.
    - consensus: council, debate, voting, peer_review, hierarchical
    - providers: openai, anthropic, google, groq, mistral, ollama, etc.
    - tools: web_search, calculator, http_request, read_file, etc.
    - rag: document_loader, pdf_loader, text_chunker, embedding, vector_search, etc.
    - memory: conversation_memory, persistent_memory, context_manager
    - logic: condition, loop, switch, merge, error_handler
    - output: text_output, json_output, file_output
    """

    def __init__(self, graph_data: Dict[str, Any]):
        self.nodes = graph_data.get("nodes", [])
        self.connections = graph_data.get("connections", [])

        # Categorized nodes
        self.triggers = []
        self.agents = []
        self.tools = []
        self.rag_nodes = []
        self.logic_nodes = []
        self.providers = []
        self.consensus_nodes = []
        self.memory_nodes = []
        self.output_nodes = []

        # Execution order
        self.execution_order: List[str] = []

    def generate_code(self) -> str:
        """Main entry point to generate the full Python script."""
        self._parse_nodes()
        self._determine_execution_order()

        script = self._generate_imports()
        script += self._generate_providers()
        script += self._generate_tools()
        script += self._generate_rag_pipeline()
        script += self._generate_memory()
        script += self._generate_agents()
        script += self._generate_consensus()
        script += self._generate_main_flow()

        return script

    def _parse_nodes(self):
        """Categorize nodes by their type."""
        for node in self.nodes:
            node_type = node.get("type", "").lower()

            # Triggers
            if node_type in ["user_input", "webhook", "schedule", "chat_trigger"]:
                self.triggers.append(node)

            # Agents
            elif node_type in ["agent", "planning_agent", "research_agent",
                              "code_review_agent", "content_writer_agent",
                              "data_analyst_agent"]:
                self.agents.append(node)

            # Tools
            elif node_type in ["tool", "web_search", "calculator", "http_request",
                              "read_file", "write_file", "database_query",
                              "send_email", "custom_tool"]:
                self.tools.append(node)

            # RAG Components
            elif node_type in ["knowledge", "document_loader", "pdf_loader",
                              "text_chunker", "embedding", "vector_store",
                              "vector_search", "hybrid_search", "reranker",
                              "query_rewriter"]:
                self.rag_nodes.append(node)

            # Logic/Control Flow
            elif node_type in ["logic", "condition", "loop", "switch",
                              "merge", "error_handler"]:
                self.logic_nodes.append(node)

            # Providers
            elif node_type in ["openai", "anthropic", "google", "groq",
                              "mistral", "ollama", "azure_openai", "cohere"]:
                self.providers.append(node)

            # Consensus
            elif node_type in ["council", "debate", "voting",
                              "peer_review", "hierarchical"]:
                self.consensus_nodes.append(node)

            # Memory
            elif node_type in ["conversation_memory", "persistent_memory",
                              "context_manager"]:
                self.memory_nodes.append(node)

            # Output
            elif node_type in ["text_output", "json_output", "file_output",
                              "webhook_response"]:
                self.output_nodes.append(node)

    def _determine_execution_order(self):
        """Topological sort based on connections."""
        # Build adjacency list
        graph: Dict[str, List[str]] = {n["id"]: [] for n in self.nodes}
        in_degree: Dict[str, int] = {n["id"]: 0 for n in self.nodes}

        for conn in self.connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            if from_id in graph and to_id in in_degree:
                graph[from_id].append(to_id)
                in_degree[to_id] += 1

        # Kahn's algorithm for topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while queue:
            node_id = queue.pop(0)
            self.execution_order.append(node_id)

            for neighbor in graph.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    def _safe_var_name(self, name: str) -> str:
        """Convert node name to valid Python variable name."""
        return name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")

    def _get_node_data(self, node: Dict, key: str, default: Any = None) -> Any:
        """Safely get data from node's data field."""
        return node.get("data", {}).get(key, default)

    def _get_connected_nodes(self, node_id: str, direction: str = "incoming") -> List[Dict]:
        """Get nodes connected to this node."""
        connected = []
        for conn in self.connections:
            if direction == "incoming" and conn.get("to") == node_id:
                source_id = conn.get("from")
                source_node = next((n for n in self.nodes if n["id"] == source_id), None)
                if source_node:
                    connected.append(source_node)
            elif direction == "outgoing" and conn.get("from") == node_id:
                target_id = conn.get("to")
                target_node = next((n for n in self.nodes if n["id"] == target_id), None)
                if target_node:
                    connected.append(target_node)
        return connected

    def _generate_imports(self) -> str:
        """Generate import statements based on used nodes."""
        imports = [
            "import asyncio",
            "from typing import Dict, List, Any, Optional",
            "from dotenv import load_dotenv",
            "",
            "# CRAFT Framework Imports",
            "from craft.agents import Agent",
        ]

        # Provider imports
        if self.providers or self.agents:
            provider_classes = []
            for p in self.providers:
                ptype = p.get("type", "openai")
                provider_classes.append(f"{ptype.title().replace('_', '')}Provider")
            if not provider_classes:
                provider_classes = ["OpenAIProvider"]
            imports.append(f"from craft.providers import {', '.join(set(provider_classes))}")

        # Tool imports
        if self.tools:
            imports.append("from craft.tools import Tool, tool")

        # RAG imports
        if self.rag_nodes:
            imports.append("from craft.rag import RetrievalEngine, DocumentChunker")
            imports.append("from craft.rag.embeddings import OpenAIEmbeddings")
            imports.append("from craft.rag.vectorstores import ChromaVectorStore")

        # Consensus imports
        if self.consensus_nodes:
            imports.append("from craft.consensus import Council, CouncilConfig")
            imports.append("from craft.consensus.strategies import VotingStrategy, DebateStrategy")

        # Memory imports
        if self.memory_nodes:
            imports.append("from craft.core import Memory, Conversation")

        imports.extend([
            "",
            "# Load environment variables",
            "load_dotenv()",
            ""
        ])

        return "\n".join(imports) + "\n"

    def _generate_providers(self) -> str:
        """Generate provider initialization code."""
        if not self.providers and not self.agents:
            return "\n# Default Provider\nprovider = OpenAIProvider()\n"

        code = "\n# --- Providers ---\n"

        for provider in self.providers:
            name = self._safe_var_name(provider.get("name", provider.get("type", "provider")))
            ptype = provider.get("type", "openai")
            model = self._get_node_data(provider, "model", "gpt-4")
            temp = self._get_node_data(provider, "temperature", 0.7)

            provider_class = f"{ptype.title().replace('_', '')}Provider"

            code += f"""
{name} = {provider_class}(
    model="{model}",
    temperature={temp}
)
"""

        # Default provider if none specified
        if not self.providers:
            code += "\n# Default Provider\nprovider = OpenAIProvider()\n"

        return code

    def _generate_tools(self) -> str:
        """Generate tool definitions."""
        if not self.tools:
            return ""

        code = "\n# --- Tools ---\n"

        for tool in self.tools:
            name = self._safe_var_name(tool.get("name", "tool"))
            tool_type = tool.get("type", "custom_tool")
            description = self._get_node_data(tool, "description", f"Tool: {name}")

            if tool_type == "web_search":
                code += f"""
@tool(name="{name}", description="{description}")
def {name}(query: str) -> str:
    \"\"\"Search the web for information.\"\"\"
    from craft.tools.builtin import duckduckgo_search
    return duckduckgo_search(query)
"""
            elif tool_type == "calculator":
                code += f"""
@tool(name="{name}", description="{description}")
def {name}(expression: str) -> str:
    \"\"\"Evaluate a mathematical expression.\"\"\"
    try:
        result = eval(expression, {{"__builtins__": {{}}}}, {{}})
        return str(result)
    except Exception as e:
        return f"Error: {{e}}"
"""
            elif tool_type == "http_request":
                code += f"""
@tool(name="{name}", description="{description}")
async def {name}(url: str, method: str = "GET", body: dict = None) -> str:
    \"\"\"Make an HTTP request.\"\"\"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, json=body)
        return response.text
"""
            else:
                # Custom tool placeholder
                code += f"""
@tool(name="{name}", description="{description}")
def {name}(input_data: str) -> str:
    \"\"\"Custom tool implementation.\"\"\"
    # TODO: Implement custom logic
    return f"Processed: {{input_data}}"
"""

        return code

    def _generate_rag_pipeline(self) -> str:
        """Generate RAG pipeline setup."""
        if not self.rag_nodes:
            return ""

        code = "\n# --- RAG Pipeline ---\n"

        # Check for specific RAG components
        has_chunker = any(n.get("type") in ["text_chunker", "document_loader", "pdf_loader"]
                        for n in self.rag_nodes)
        has_embedding = any(n.get("type") == "embedding" for n in self.rag_nodes)
        has_vectorstore = any(n.get("type") == "vector_store" for n in self.rag_nodes)
        has_search = any(n.get("type") in ["vector_search", "hybrid_search"]
                        for n in self.rag_nodes)

        if has_chunker:
            code += """
# Document Chunker
chunker = DocumentChunker(
    chunk_size=512,
    chunk_overlap=50,
    strategy="sentence"
)
"""

        if has_embedding:
            code += """
# Embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
"""

        if has_vectorstore:
            code += """
# Vector Store
vectorstore = ChromaVectorStore(
    collection_name="craft_docs",
    embeddings=embeddings
)
"""

        if has_search:
            code += """
# Retrieval Engine
retrieval_engine = RetrievalEngine(
    vectorstore=vectorstore,
    top_k=5,
    use_reranking=True
)
"""

        return code

    def _generate_memory(self) -> str:
        """Generate memory configuration."""
        if not self.memory_nodes:
            return ""

        code = "\n# --- Memory ---\n"

        for mem_node in self.memory_nodes:
            mem_type = mem_node.get("type", "conversation_memory")
            name = self._safe_var_name(mem_node.get("name", "memory"))

            if mem_type == "persistent_memory":
                code += f"""
{name} = Memory(
    storage_type="sqlite",
    database_path="./craft_memory.db"
)
"""
            else:
                code += f"""
{name} = Memory(max_messages=100)
"""

        return code

    def _generate_agents(self) -> str:
        """Generate agent definitions."""
        if not self.agents:
            return ""

        code = "\n# --- Agents ---\n"

        for agent in self.agents:
            name = self._safe_var_name(agent.get("name", "agent"))
            agent_type = agent.get("type", "agent")
            role = self._get_node_data(agent, "role", "Assistant")
            goal = self._get_node_data(agent, "goal", "Help the user accomplish their task")
            system_prompt = self._get_node_data(agent, "system_prompt", "")

            # Find connected tools
            connected_tools = self._get_connected_nodes(agent["id"], "incoming")
            tool_names = [self._safe_var_name(t.get("name", "tool"))
                         for t in connected_tools if t.get("type") in
                         ["tool", "web_search", "calculator", "http_request",
                          "read_file", "write_file", "custom_tool"]]

            # Find connected provider
            connected_providers = [n for n in self._get_connected_nodes(agent["id"], "incoming")
                                  if n.get("type") in ["openai", "anthropic", "google",
                                                       "groq", "mistral", "ollama"]]
            provider_var = self._safe_var_name(connected_providers[0].get("name", "provider")) \
                          if connected_providers else "provider"

            tools_str = f"[{', '.join(tool_names)}]" if tool_names else "[]"

            # System prompt handling
            system_prompt_line = ""
            if system_prompt:
                escaped_prompt = system_prompt.replace('"', '\\"').replace('\n', '\\n')
                system_prompt_line = f'\n    system_prompt="{escaped_prompt}",'

            code += f"""
{name} = Agent(
    name="{agent.get('name', 'Agent')}",
    role="{role}",
    goal="{goal}",{system_prompt_line}
    provider={provider_var},
    tools={tools_str}
)
"""

        return code

    def _generate_consensus(self) -> str:
        """Generate consensus/council setup."""
        if not self.consensus_nodes:
            return ""

        code = "\n# --- Consensus ---\n"

        for consensus in self.consensus_nodes:
            name = self._safe_var_name(consensus.get("name", "council"))
            strategy = consensus.get("type", "voting")

            # Find connected agents
            connected_agents = [n for n in self._get_connected_nodes(consensus["id"], "incoming")
                               if "agent" in n.get("type", "")]
            agent_names = [self._safe_var_name(a.get("name", "agent")) for a in connected_agents]
            agents_str = f"[{', '.join(agent_names)}]" if agent_names else "[]"

            if strategy == "voting":
                code += f"""
{name} = Council(
    agents={agents_str},
    strategy=VotingStrategy(vote_type="majority"),
    max_rounds=3
)
"""
            elif strategy == "debate":
                code += f"""
{name} = Council(
    agents={agents_str},
    strategy=DebateStrategy(max_rounds=5),
    chairman={agent_names[0] if agent_names else "None"}
)
"""
            else:
                code += f"""
{name} = Council(
    agents={agents_str},
    max_rounds=3
)
"""

        return code

    def _generate_main_flow(self) -> str:
        """Generate the main execution flow."""
        code = "\n# --- Main Execution Flow ---\n"

        # Determine entry point
        if self.triggers:
            trigger = self.triggers[0]
            trigger_type = trigger.get("type", "user_input")

            if trigger_type == "user_input":
                code += """
async def main(user_input: str = None):
    if user_input is None:
        user_input = input("Enter your request: ")

    print("🚀 Starting CRAFT Workflow...")
"""
            elif trigger_type == "webhook":
                code += """
from fastapi import FastAPI, Request
app = FastAPI()

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
"""
            else:
                code += """
async def main(user_input: str = "Execute the workflow"):
    print("🚀 Starting CRAFT Workflow...")
"""
        else:
            code += """
async def main(user_input: str = "Execute the workflow"):
    print("🚀 Starting CRAFT Workflow...")
"""

        # Execute agents in order
        if self.agents:
            for i, agent in enumerate(self.agents):
                name = self._safe_var_name(agent.get("name", "agent"))

                if i == 0:
                    code += f"""
    # Execute {agent.get('name', 'Agent')}
    result = await {name}.arun(user_input)
    print(f"📝 {agent.get('name', 'Agent')} Response: {{result.text}}")
"""
                else:
                    code += f"""
    # Execute {agent.get('name', 'Agent')}
    result = await {name}.arun(result.text)
    print(f"📝 {agent.get('name', 'Agent')} Response: {{result.text}}")
"""

        # Execute consensus if present
        if self.consensus_nodes:
            council = self.consensus_nodes[0]
            name = self._safe_var_name(council.get("name", "council"))
            code += f"""
    # Run Council for consensus
    council_result = await {name}.deliberate(user_input)
    print(f"🏛️ Council Decision: {{council_result.decision}}")
"""

        # Output handling
        code += """
    return result

if __name__ == "__main__":
    asyncio.run(main())
"""

        return code

    def to_json(self) -> str:
        """Export the parsed graph as JSON for debugging."""
        return json.dumps({
            "nodes": self.nodes,
            "connections": self.connections,
            "execution_order": self.execution_order,
            "categories": {
                "triggers": [n["id"] for n in self.triggers],
                "agents": [n["id"] for n in self.agents],
                "tools": [n["id"] for n in self.tools],
                "rag": [n["id"] for n in self.rag_nodes],
                "logic": [n["id"] for n in self.logic_nodes],
                "consensus": [n["id"] for n in self.consensus_nodes],
            }
        }, indent=2)


# ============================================================================
# API Endpoint for Export
# ============================================================================

def create_export_server():
    """Create a FastAPI server for the export endpoint."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI(title="CRAFT Stitch Export API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class GraphData(BaseModel):
        nodes: List[Dict[str, Any]]
        connections: List[Dict[str, Any]]

    @app.post("/api/export")
    async def export_workflow(data: GraphData):
        try:
            parser = GraphParser(data.model_dump())
            code = parser.generate_code()
            return {"success": True, "code": code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.post("/api/validate")
    async def validate_workflow(data: GraphData):
        try:
            parser = GraphParser(data.model_dump())
            parser._parse_nodes()
            parser._determine_execution_order()

            return {
                "success": True,
                "summary": {
                    "total_nodes": len(data.nodes),
                    "agents": len(parser.agents),
                    "tools": len(parser.tools),
                    "rag_components": len(parser.rag_nodes),
                    "connections": len(data.connections),
                    "execution_order": parser.execution_order
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return app


if __name__ == "__main__":
    # Run the export server
    import uvicorn
    app = create_export_server()
    uvicorn.run(app, host="0.0.0.0", port=8001)
