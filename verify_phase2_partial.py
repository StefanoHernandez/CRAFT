import asyncio
import os
os.environ["CRAFT_TRACE_CLIENT_IO"] = "1"
from craft.agents import Agent
from craft.providers import Provider, ProviderConfig
# from craft.types import AgentConfig

# Mock Provider to avoid real API Calls
class MockProvider(Provider):
    async def chat(self, messages, **kwargs):
        return "I am a simulated response from the partial execution."

    async def _achat(self, messages, **kwargs):
         return "I am a simulated response from the partial execution."

    def _chat(self, messages, **kwargs):
         return "I am a simulated response from the partial execution."

    def _validate_config(self):
        pass

async def test_partial_execution_logic():
    print("🧪 Testing Partial Execution Logic...")
    
    # Simulate the payload received by /api/run_node
    node_payload = {
        "id": "node_test",
        "type": "agent",
        "name": "TestRunner",
        "data": {
            "role": "Tester",
            "goal": "Verify logic"
        }
    }
    user_input = "Hello Node!"
    
    print(f"🔹 Simulating execution for node: {node_payload['name']}")
    
    # Logic extracted from unified-serve.py
    try:
        if node_payload.get("type") == "agent":
            agent_name = node_payload.get("name", "TempAgent")
            role = node_payload.get("data", {}).get("role", "Assistant")
            goal = node_payload.get("data", {}).get("goal", "Help the user")
            
            # Use Mock Provider
            provider = MockProvider(config=ProviderConfig(model="mock-model"))
            
            agent = Agent(
                name=agent_name,
                role=role,
                goal=goal,
                provider=provider
            )
            
            print("✅ Agent instantiated successfully.")
            
            # Execute
            print(f"🔹 Running agent with input: '{user_input}'...")
            result = await agent.arun(user_input)
            
            print(f"✅ Result received: {result.text}")
            assert result.text == "I am a simulated response from the partial execution."
            print("✅ Verification Passed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(test_partial_execution_logic())
