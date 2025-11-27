
import os
from craft.agents import Agent
from craft.providers import AnthropicProvider, OpenAIProvider
from craft.tools import tool

# 1. Define custom tools
@tool
def calculate_area(length: float, width: float) -> float:
    """
    Calculate the area of a rectangle.
    
    Args:
        length: The length of the rectangle
        width: The width of the rectangle
    """
    return length * width

@tool
def get_material_cost(material: str) -> float:
    """
    Get the cost per square meter of a material.
    
    Args:
        material: The material name (wood, tile, carpet)
    """
    costs = {"wood": 50.0, "tile": 30.0, "carpet": 20.0}
    return costs.get(material.lower(), 100.0)

# 2. Configure Provider
# You can switch between providers easily
provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
# provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

# 3. Create the Agent
estimator_agent = Agent(
    name="Estimator",
    role="Construction Estimator",
    goal="Calculate accurate material costs for flooring projects",
    backstory="You are an experienced contractor who helps clients estimate renovation costs.",
    provider=provider,
    tools=[calculate_area, get_material_cost],
    verbose=True  # Print steps to console
)

# 4. Run the Agent
task = "I need to floor a room that is 5 meters by 4 meters with wood. How much will it cost?"
print(f"Task: {task}\n")

result = estimator_agent.run(task)

print("\n--- Final Answer ---")
print(result.text)
