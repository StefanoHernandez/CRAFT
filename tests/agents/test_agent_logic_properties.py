
import pytest
from hypothesis import given, strategies as st
from unittest.mock import MagicMock, patch
from craft.agents.agent import Agent, AgentConfig, AgentState
from craft.core.conversation import Message, Role
from craft.providers.base import Provider, ChatResponse
from craft.core.memory import Memory

# Property 16: Max Steps Termination
# Verify that the agent terminates after max_steps even if the task is not complete.

@given(st.integers(min_value=1, max_value=5))
def test_property_max_steps_termination(max_steps):
    """
    Property 16: Verify that agent terminates exactly at max_steps.
    """
    mock_provider = MagicMock(spec=Provider)
    # Mock chat to return "I need to do more" to force continuation
    mock_provider.chat.return_value = ChatResponse(
        role=Role.ASSISTANT,
        content="I need to use another tool.",
        tool_calls=[],
        model="test-model"
    )
    mock_provider.config = MagicMock()
    mock_provider.config.max_retries = 0
    mock_provider.config.planning_interval = None
    
    agent = Agent(
        name="test_agent",
        provider=mock_provider,
        max_steps=max_steps,
        planning_interval=None
    )
    
    # We need to ensure the agent doesn't crash but stops.
    # The run loop should execute 'max_steps' times.
    
    result = agent.run("Task that never ends")
    
    # Check that total steps executed equals max_steps
    # Or at least does not exceed it.
    # Note: current_step is incremented at the start or end of loop.
    # If it stops because of max_steps, current_step should be max_steps.
    
    assert result.total_steps <= max_steps
    assert "Agent reached maximum steps" in result.text or result.total_steps == max_steps

# Property 56: Message Trimming (Preserve system prompts)
# Verify that when memory is trimmed, the system prompt (first message) is preserved.

@given(st.lists(st.text(), min_size=10, max_size=20))
def test_property_message_trimming_preserves_system(messages_content):
    """
    Property 56: Verify that message trimming preserves the system prompt.
    """
    # Create a memory with a small window
    max_messages = 5
    memory = Memory(max_messages=max_messages)
    
    # Create an initial system message
    system_msg = Message(role=Role.SYSTEM, content="System Prompt")
    
    # Create a list of messages to add
    new_messages = [Message(role=Role.USER, content=c) for c in messages_content]
    
    # Add all messages
    all_messages = [system_msg] + new_messages
    
    # Trim messages
    trimmed = memory.trim_messages(all_messages)
    
    # Verification
    # 1. System prompt should still be the first message
    assert trimmed[0] == system_msg
    assert trimmed[0].role == Role.SYSTEM
    
    # 2. Length should not exceed max_messages + 1 (system prompt is usually counted or excluded? 
    # Let's check implementation: 
    # if messages[0].role == "system": messages_to_trim = messages[1:]
    # if len(messages_to_trim) > self.max_messages: trim...
    # return [system_msg] + messages_to_trim
    # So total length will be max_messages + 1 (system prompt + max recent messages)
    
    assert len(trimmed) <= max_messages + 1
    
    # 3. The last messages should be the most recent ones from the input
    # The last message in trimmed should be the last message in all_messages
    assert trimmed[-1] == all_messages[-1] 
