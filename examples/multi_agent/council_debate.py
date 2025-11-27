
import os
from craft.agents import Agent
from craft.providers import AnthropicProvider
from craft.consensus import Council, DebateStrategy
from craft.tools import tool

# Define tools
@tool
def search_web(query: str) -> str:
    """Mock web search."""
    return f"Search results for {query}: Python 3.12 was released in Oct 2023."

# Create Agents with different perspectives
provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))

researcher = Agent(
    name="Researcher",
    role="Tech Researcher",
    goal="Find accurate technical facts",
    provider=provider,
    tools=[search_web]
)

skeptic = Agent(
    name="Skeptic",
    role="Critical Reviewer",
    goal="Challenge assumptions and verify facts",
    provider=provider
)

writer = Agent(
    name="Writer",
    role="Technical Writer",
    goal="Synthesize information into a clear summary",
    provider=provider
)

# Create a Council for collaboration
council = Council(
    agents=[researcher, skeptic, writer],
    strategy=DebateStrategy(rounds=2),  # They will debate for 2 rounds
    verbose=True
)

# Run the collaboration
topic = "What are the key features of Python 3.12?"
print(f"Topic: {topic}\n")

result = council.decide(topic)

print("\n--- Consensus Result ---")
print(result)
