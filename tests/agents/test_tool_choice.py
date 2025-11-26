"""Tests for tool choice control."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from craft.agents import Agent
from craft.providers.base import Provider, ChatResponse, Role
from craft.tools.base import Tool, ToolMetadata, ToolParameter

class MockProvider(Provider):
    def __init__(self):
        super().__init__(config=MagicMock())
        self.config.model = "mock-model"
        self.config.api_key = "mock-key"
        self._chat_mock = MagicMock(return_value=ChatResponse(content="test", role=Role.ASSISTANT, model="mock"))
        self._achat_mock = AsyncMock(return_value=ChatResponse(content="test", role=Role.ASSISTANT, model="mock"))
        
    def _validate_config(self):
        pass
        
    @property
    def name(self):
        return "mock"

    def chat(self, messages, stream=False, **kwargs):
        return self._chat_mock(messages, stream=stream, **kwargs)

    async def achat(self, messages, stream=False, **kwargs):
        return await self._achat_mock(messages, stream=stream, **kwargs)

def create_mock_tool(name):
    return Tool(
        name=name,
        description=f"Mock tool {name}",
        func=lambda x: x,
        metadata=ToolMetadata(
            name=name,
            description=f"Mock tool {name}",
            parameters=[ToolParameter(name="arg", type="str")],
            return_type="str",
            json_schema={"type": "function", "function": {"name": name}}
        )
    )

@pytest.fixture
def provider():
    return MockProvider()

@pytest.fixture
def tools():
    return [create_mock_tool("tool_a"), create_mock_tool("tool_b")]

@pytest.fixture
def agent(provider, tools):
    return Agent(name="test_agent", provider=provider, tools=tools)

def test_tool_choice_auto(agent, provider):
    """Test default tool_choice='auto'."""
    agent.run("task")
    
    # Verify provider called with all tools and tool_choice='auto'
    call_args = provider._chat_mock.call_args
    assert call_args.kwargs["tool_choice"] == "auto"
    assert len(call_args.kwargs["tools"]) == 2

def test_tool_choice_none(agent, provider):
    """Test tool_choice='none'."""
    agent.run("task", tool_choice="none")
    
    call_args = provider._chat_mock.call_args
    assert call_args.kwargs["tool_choice"] == "none"
    # Tools should still be passed, but provider handles 'none'
    assert len(call_args.kwargs["tools"]) == 2

def test_tool_choice_required(agent, provider):
    """Test tool_choice='required'."""
    agent.run("task", tool_choice="required")
    
    call_args = provider._chat_mock.call_args
    assert call_args.kwargs["tool_choice"] == "required"

def test_tool_choice_specific_tool(agent, provider):
    """Test forcing a specific tool."""
    agent.run("task", tool_choice="tool_a")
    
    call_args = provider._chat_mock.call_args
    assert call_args.kwargs["tool_choice"] == "tool_a"

def test_tool_choice_list(agent, provider):
    """Test filtering tools with a list."""
    agent.run("task", tool_choice=["tool_a"])
    
    call_args = provider._chat_mock.call_args
    # Should pass list as tool_choice (Agent passes it through, Provider formats it)
    assert call_args.kwargs["tool_choice"] == ["tool_a"]
    # Should filter tools list passed to provider
    assert len(call_args.kwargs["tools"]) == 1
    assert call_args.kwargs["tools"][0].name == "tool_a"

def test_invalid_tool_choice(agent):
    """Test invalid tool choice raises error."""
    from craft.core.errors import AgentExecutionError
    
    with pytest.raises(AgentExecutionError) as excinfo:
        agent.run("task", tool_choice="non_existent_tool")
    assert "not found" in str(excinfo.value)
        
    with pytest.raises(AgentExecutionError) as excinfo:
        agent.run("task", tool_choice=["tool_a", "non_existent_tool"])
    assert "not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_async_tool_choice(agent, provider):
    """Test async execution handles tool_choice."""
    await agent.arun("task", tool_choice="required")
    
    call_args = provider._achat_mock.call_args
    assert call_args.kwargs["tool_choice"] == "required"
