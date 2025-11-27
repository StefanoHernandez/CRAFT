
import pytest
from hypothesis import given, strategies as st
from unittest.mock import MagicMock, patch
from craft.core.errors import CRAFTError, ToolExecutionError, ProviderError
from craft.agents.agent import Agent, AgentConfig
from craft.tools.base import Tool, ToolMetadata
from craft.providers.base import Provider, ChatResponse
from craft.core.conversation import Message
from craft.providers.base import Role

# Property 59: Tool Error Capture
# Verify that exceptions raised in tools are captured as ToolExecutionError
# and contain the original error message.

# Property 59: Tool Error Capture
# Verify that exceptions raised in tools are captured as ToolExecutionError
# and contain the original error message.

# Property 59: Tool Error Capture
# Verify that exceptions raised in tools are captured as ToolExecutionError
# and contain the original error message.

def failing_function(**kwargs):
    raise ValueError(kwargs.get("error_message", "Something went wrong"))

@given(st.text())
def test_property_tool_error_capture(error_message):
    """
    Property 59: Verify that tool errors are captured and wrapped correctly.
    """
    # Create tool with a failing function
    # We need to pass the error message to the function somehow, or patch it.
    # Since we use hypothesis, we generate error_message.
    # We can create a closure or partial, or just patch it.
    
    tool = Tool(
        name="falsy_tool",
        description="A tool that always fails",
        func=failing_function,
        metadata=ToolMetadata(
            name="falsy_tool",
            description="A tool that always fails",
            parameters=[],
            return_type="str",
            json_schema={}
        )
    )
    
    # We patch the function on the instance to raise the specific error message
    tool.func = MagicMock(side_effect=ValueError(error_message))
    
    try:
        tool()
    except ToolExecutionError as e:
        assert tool.name in e.tool_name
        assert error_message in str(e)
        assert e.original_exception is not None
        assert isinstance(e.original_exception, ValueError)
    except Exception as e:
        pytest.fail(f"Expected ToolExecutionError, got {type(e).__name__}: {e}")

# Property 60: Graceful Termination
# Verify that the agent terminates gracefully even when steps fail repeatedly.

@given(st.integers(min_value=1, max_value=5))
def test_property_graceful_termination(max_steps):
    """
    Property 60: Verify that agent terminates gracefully upon reaching max steps
    even if errors occur during execution.
    """
    # Mock provider to always raise an error or return garbage
    mock_provider = MagicMock(spec=Provider)
    # Mock config object on provider
    mock_provider.config = MagicMock()
    mock_provider.config.max_retries = 0
    mock_provider.config.planning_interval = None # Disable planning for this test
    
    # Mock chat to raise exception
    mock_provider.chat.side_effect = Exception("Provider failure")
    
    agent = Agent(
        name="test_agent",
        provider=mock_provider,
        role="tester",
        goal="test termination",
        max_steps=max_steps,
        planning_interval=None # Disable planning
    )
    
    # Run the agent
    result = agent.run("Do something")
    
    assert result is not None
    # Depending on implementation, it might return "Agent failed" or "Task stopped"
    assert "Agent failed" in result.text or "Task stopped" in result.text

# Property 61: Provider Error Messages
# Verify that ProviderError contains retryable status and suggestions.

@given(st.booleans(), st.text())
def test_property_provider_error_messages(retryable, suggestion):
    """
    Property 61: Verify ProviderError attributes.
    """
    error = ProviderError(
        message="API Error",
        provider_name="TestProvider",
        retryable=retryable,
        recovery_suggestion=suggestion
    )
    
    assert error.retryable == retryable
    assert error.recovery_suggestion == suggestion
    assert "Suggestion" in str(error) if suggestion else True
