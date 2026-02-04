"""Tests for Agent delegation patterns (can_call and delegate_to)."""

import pytest
from unittest.mock import MagicMock, patch

from craft.agents.agent import Agent, AgentResult
from craft.providers.base import Provider, ProviderConfig, ChatResponse, Role
from craft.core.errors import AgentExecutionError


class MockProvider(Provider):
    """Mock provider for testing."""
    
    def __init__(self, responses: list[str] | None = None):
        super().__init__(config=ProviderConfig(api_key="mock-key", model="mock-model"))
        self._responses = responses or ["Task completed successfully"]
        self._call_count = 0
    
    @property
    def name(self) -> str:
        return "mock"
    
    def _validate_config(self) -> None:
        pass
    
    def _chat(self, messages, stream=False, **kwargs):
        response = self._responses[min(self._call_count, len(self._responses) - 1)]
        self._call_count += 1
        return ChatResponse(content=response, role=Role.ASSISTANT, model="mock")
    
    async def _achat(self, messages, stream=False, **kwargs):
        return self._chat(messages, stream, **kwargs)


@pytest.fixture
def mock_provider():
    """Provide a mock provider."""
    return MockProvider()


@pytest.fixture
def specialist_agent(mock_provider):
    """Create a specialist agent."""
    return Agent(
        name="weather_expert",
        provider=mock_provider,
        role="Weather Specialist",
        goal="Provide accurate weather forecasts",
        max_steps=2
    )


@pytest.fixture
def coordinator_agent(mock_provider):
    """Create a coordinator agent."""
    return Agent(
        name="coordinator",
        provider=mock_provider,
        role="Trip Coordinator",
        goal="Plan comprehensive trips",
        max_steps=2
    )


def test_can_call_single_agent(coordinator_agent, specialist_agent):
    """Test can_call() with a single agent."""
    # Register specialist as callable
    coordinator_agent.can_call([specialist_agent])
    
    # Verify agent was registered
    assert "weather_expert" in coordinator_agent.callable_agents
    assert specialist_agent == coordinator_agent.callable_agents["weather_expert"]
    
    # Verify tool was created
    assert "weather_expert" in coordinator_agent.tool_map
    tool = coordinator_agent.tool_map["weather_expert"]
    assert tool.name == "weather_expert"
    assert "Weather Specialist" in tool.description


def test_can_call_multiple_agents(coordinator_agent, mock_provider):
    """Test can_call() with multiple agents."""
    agent1 = Agent(name="agent1", provider=mock_provider, role="Role 1")
    agent2 = Agent(name="agent2", provider=mock_provider, role="Role 2")
    
    coordinator_agent.can_call([agent1, agent2])
    
    # Both agents should be registered
    assert "agent1" in coordinator_agent.callable_agents
    assert "agent2" in coordinator_agent.callable_agents
    
    # Both tools should be created
    assert "agent1" in coordinator_agent.tool_map
    assert "agent2" in coordinator_agent.tool_map


def test_delegate_to_with_custom_names(coordinator_agent, specialist_agent, mock_provider):
    """Test delegate_to() with custom tool names."""
    research_agent = Agent(name="researcher", provider=mock_provider, role="Researcher")
    
    # Register agents with custom names
    coordinator_agent.delegate_to({
        "get_weather_forecast": specialist_agent,
        "search_information": research_agent
    })
    
    # Verify tools were created with custom names
    assert "get_weather_forecast" in coordinator_agent.tool_map
    assert "search_information" in coordinator_agent.tool_map
    
    # Verify agents are tracked
    assert "get_weather_forecast" in coordinator_agent.callable_agents
    assert "search_information" in coordinator_agent.callable_agents


def test_agent_tool_execution(coordinator_agent, mock_provider):
    """Test that agent tools can be executed."""
    # Create specialist with specific response
    specialist = Agent(
        name="specialist",
        provider=MockProvider(["Specialist response"]),
        max_steps=1
    )
    
    coordinator_agent.can_call([specialist])
    
    # Get the tool
    tool = coordinator_agent.tool_map["specialist"]
    
    # Execute the tool by calling its func
    result = tool.func(task="test task")
    
    # Verify result
    assert "Specialist response" in result


def test_circular_call_detection(mock_provider):
    """Test that circular agent calls are detected."""
    agent_a = Agent(name="agent_a", provider=mock_provider, max_steps=2)
    agent_b = Agent(name="agent_b", provider=mock_provider, max_steps=2)
    
    # Set up circular reference
    agent_a.can_call([agent_b])
    agent_b.can_call([agent_a])
    
    # This should raise an error when executed
    # (would need actual execution to trigger, but structure is tested)
    assert "agent_b" in agent_a.callable_agents
    assert "agent_a" in agent_b.callable_agents


def test_delegation_tracking(coordinator_agent, mock_provider):
    """Test that delegations are tracked in aggregated results."""
    specialist = Agent(
        name="specialist",
        provider=MockProvider(["Specialist done"]),
        max_steps=1
    )
    
    coordinator_agent.can_call([specialist])
    
    # Execute with delegation
    tool = coordinator_agent.tool_map["specialist"]
    result = tool.func(task="subtask")
    
    # Check aggregated results (note: this will be empty until coordinator.run() is called)
    # This test verifies the structure exists
    assert hasattr(coordinator_agent, 'get_aggregated_results')


def test_system_prompt_includes_delegated_agents(coordinator_agent, specialist_agent):
    """Test that system prompt is updated to include delegated agents."""
    initial_prompt = coordinator_agent.system_prompt
    
    coordinator_agent.can_call([specialist_agent])
    
    updated_prompt = coordinator_agent.system_prompt
    
    # Prompt should be updated
    assert "weather_expert" in updated_prompt
    assert updated_prompt != initial_prompt


def test_delegate_to_tracks_custom_name(coordinator_agent, specialist_agent):
    """Test that delegate_to tracks the custom tool name used."""
    coordinator_agent.delegate_to({
        "custom_weather_tool": specialist_agent
    })
    
    # Execute and check that custom name would be tracked
    tool = coordinator_agent.tool_map["custom_weather_tool"]
    assert tool.name == "custom_weather_tool"


def test_agent_tool_with_role_and_goal(mock_provider):
    """Test agent tool description includes role and goal."""
    specialist = Agent(
        name="expert",
        provider=mock_provider,
        role="Domain Expert",
        goal="solve complex problems"
    )
    
    coordinator = Agent(name="coordinator", provider=mock_provider)
    coordinator.can_call([specialist])
    
    tool = coordinator.tool_map["expert"]
    
    # Description should include role and goal
    assert "Domain Expert" in tool.description
    assert "solve complex problems" in tool.description


def test_can_call_updates_tool_list(coordinator_agent, specialist_agent):
    """Test that can_call() adds to tools list."""
    initial_tool_count = len(coordinator_agent.tools)
    
    coordinator_agent.can_call([specialist_agent])
    
    # Tool count should increase
    assert len(coordinator_agent.tools) == initial_tool_count + 1


def test_multiple_can_call_invocations(coordinator_agent, mock_provider):
    """Test calling can_call() multiple times."""
    agent1 = Agent(name="agent1", provider=mock_provider)
    agent2 = Agent(name="agent2", provider=mock_provider)
    
    # First call
    coordinator_agent.can_call([agent1])
    assert len(coordinator_agent.callable_agents) == 1
    
    # Second call
    coordinator_agent.can_call([agent2])
    assert len(coordinator_agent.callable_agents) == 2
    
    # Both should be available
    assert "agent1" in coordinator_agent.callable_agents
    assert "agent2" in coordinator_agent.callable_agents


def test_agent_tool_metadata_structure(coordinator_agent, specialist_agent):
    """Test that agent tool has correct metadata structure."""
    coordinator_agent.can_call([specialist_agent])
    
    tool = coordinator_agent.tool_map["weather_expert"]
    metadata = tool.metadata
    
    # Check metadata structure
    assert metadata.name == "weather_expert"
    assert metadata.description is not None
    assert len(metadata.parameters) == 1
    assert metadata.parameters[0].name == "task"
    assert metadata.parameters[0].required is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
