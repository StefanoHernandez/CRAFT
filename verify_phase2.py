import asyncio
import json
# from craft.api.websocket import manager # Removed to avoid dependency issues during logic test
 # Mocking the server environment
from stitch.graph_parser import GraphParser

# Sample Stitch JSON (Mock)
mock_workflow = {
    "nodes": [
        {
            "id": "node_1",
            "type": "agent",
            "name": "Researcher",
            "data": {"role": "Researcher", "goal": "Find info"}
        },
        {
            "id": "node_2",
            "type": "tool",
            "name": "Google Search",
            "data": {}
        }
    ],
    "connections": [
        {"from": "node_2", "to": "node_1"}
    ]
}

def test_graph_parser():
    print("🧪 Testing GraphParser Logic...")
    parser = GraphParser(mock_workflow)
    code = parser.generate_code()
    
    assert "class Researcher" not in code # Agents are instances not classes in this version
    assert "researcher = Agent(" in code
    assert "Google Search" in code
    assert "tools=[google_search]" in code
    
    print("✅ GraphParser generated valid code structure:")
    print("-" * 40)
    print(code[:300] + "...\n[truncated]\n")
    print("-" * 40)

if __name__ == "__main__":
    test_graph_parser()
