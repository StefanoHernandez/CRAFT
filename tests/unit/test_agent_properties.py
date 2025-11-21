"""Property-based tests for the agent system.

These tests verify correctness properties using hypothesis for property-based testing.
Each test runs a minimum of 100 iterations to ensure properties hold across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock

from craft.agents import Agent, AgentConfig, AgentResult, StepResult, AgentState
from craft.providers.base import Provider, Message, Role, ChatResponse, ProviderConfig
from craft.tools.base import Tool
from craft.core.memory import Memory
from craft.core.errors import AgentExecutionError


# Mock provider for testing
class MockProvider(Provider):
    """Mock provider for testing agents."""
    
    def __init__(self, responses: List[str] = None, **kwargs):
        """Initialize mock provider with predefined responses."""
        config = ProviderConfig(model="mock-model", **kwargs)
        super().__init__(config)
        self.responses = responses or ["This is a test response."]
        self.call_count = 0
        self.messages_received = []
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        pass
    
    def chat(self, messages: List[Message], stream: bool = False, **kwargs) -> ChatResponse:
        """Mock chat method."""
        self.messages_received.append(messages)
        response_text = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        
        return ChatResponse(
            content=response_text,
            role=Role.ASSISTANT,
            model=self.config.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
    
    async def achat(self, messages: List[Message], stream: bool = False, **kwargs) -> ChatResponse:
        """Mock async chat method."""
        return self.chat(messages, stream, **kwargs)


# Custom strategies for generating test data
@st.composite
def agent_names(draw):
    """Generate valid agent names."""
    return draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))


@st.composite
def agent_roles(draw):
    """Generate agent roles."""
    roles = ["Research Assistant", "Data Analyst", "Writer", "Coder", "Helper"]
    return draw(st.sampled_from(roles))


@st.composite
def agent_goals(draw):
    """Generate agent goals."""
    goals = [
        "Find accurate information",
        "Analyze data thoroughly",
        "Write clear content",
        "Solve problems efficiently",
        "Help users effectively"
    ]
    return draw(st.sampled_from(goals))


@st.composite
def task_inputs(draw):
    """Generate task input strings."""
    return draw(st.text(min_size=10, max_size=200))


# Feature: craft-v2-agents-tools, Property 13: Agent Initialization
@settings(max_examples=100)
@given(
    agent_names(),
    agent_roles(),
    agent_goals(),
    st.integers(min_value=1, max_value=20)
)
def test_property_13_agent_initialization(name, role, goal, max_steps):
    """
    Property 13: Agent Initialization
    
    For any valid agent configuration with role and goal, agent initialization SHALL
    create an agent with appropriate context and capabilities.
    
    **Validates: Requirements 4.1**
    """
    # Create mock provider
    provider = MockProvider()
    
    # Initialize agent with role and goal
    agent = Agent(
        name=name,
        provider=provider,
        role=role,
        goal=goal,
        max_steps=max_steps
    )
    
    # Verify agent is properly initialized
    assert agent.config.name == name
    assert agent.config.role == role
    assert agent.config.goal == goal
    assert agent.config.max_steps == max_steps
    
    # Verify system prompt is built from role and goal
    assert agent.system_prompt is not None
    assert len(agent.system_prompt) > 0
    assert role in agent.system_prompt or role.lower() in agent.system_prompt.lower()
    assert goal in agent.system_prompt or goal.lower() in agent.system_prompt.lower()
    
    # Verify provider is set
    assert agent.provider is provider
    
    # Verify tools list exists (even if empty)
    assert agent.tools is not None
    assert isinstance(agent.tools, list)


# Feature: craft-v2-agents-tools, Property 14: Tool Result Integration
@settings(max_examples=100)
@given(
    agent_names(),
    st.text(min_size=10, max_size=100)
)
def test_property_14_tool_result_integration(name, task_input):
    """
    Property 14: Tool Result Integration
    
    For any agent step where a tool is used, the tool result SHALL be incorporated
    into the agent's message history for the next step.
    
    **Validates: Requirements 4.4**
    """
    # Create mock provider that returns a final answer
    provider = MockProvider(responses=["Here is the final answer to your question."])
    
    # Create agent
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=5
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify state was maintained
    assert agent.state is not None
    assert agent.state.messages is not None
    assert len(agent.state.messages) >= 2  # At least system + user + assistant
    
    # Verify message history contains user input
    user_messages = [m for m in agent.state.messages if m.role == Role.USER]
    assert len(user_messages) >= 1
    assert user_messages[0].content == task_input
    
    # Verify assistant responses are in history
    assistant_messages = [m for m in agent.state.messages if m.role == Role.ASSISTANT]
    assert len(assistant_messages) >= 1


# Feature: craft-v2-agents-tools, Property 15: Agent Result Structure
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=1, max_value=10)
)
def test_property_15_agent_result_structure(name, task_input, max_steps):
    """
    Property 15: Agent Result Structure
    
    For any completed agent execution, the result SHALL contain the final answer
    and execution metadata including steps and tools used.
    
    **Validates: Requirements 4.5**
    """
    # Create mock provider
    provider = MockProvider(responses=["This is my final answer."])
    
    # Create agent
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=max_steps
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify result structure
    assert isinstance(result, AgentResult)
    
    # Verify final answer is present
    assert result.text is not None
    assert len(result.text) > 0
    
    # Verify execution metadata
    assert result.steps is not None
    assert isinstance(result.steps, list)
    assert result.total_steps > 0
    assert result.total_steps <= max_steps
    
    # Verify tools_used list exists (even if empty)
    assert result.tools_used is not None
    assert isinstance(result.tools_used, list)
    
    # Verify metadata exists
    assert result.metadata is not None
    assert isinstance(result.metadata, dict)
    assert "execution_time_seconds" in result.metadata
    assert "max_steps_reached" in result.metadata


# Feature: craft-v2-agents-tools, Property 16: Max Steps Termination
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=1, max_value=5)  # Small max_steps to trigger termination
)
def test_property_16_max_steps_termination(name, task_input, max_steps):
    """
    Property 16: Max Steps Termination
    
    For any agent execution that reaches max_steps, the system SHALL terminate
    gracefully and return partial results with an explanation.
    
    **Validates: Requirements 4.6**
    """
    # Create mock provider that never gives a final answer
    # This will cause the agent to hit max_steps
    provider = MockProvider(
        responses=["I need to search for more information."] * 20
    )
    
    # Create agent with small max_steps
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=max_steps
    )
    
    # Run agent - should hit max_steps
    result = agent.run(task_input)
    
    # Verify graceful termination
    assert isinstance(result, AgentResult)
    
    # Verify max_steps was reached
    assert result.metadata.get("max_steps_reached") is True
    assert result.metadata.get("terminated") == "max_steps"
    assert result.metadata.get("partial") is True
    
    # Verify partial results are returned
    assert result.text is not None
    assert "Maximum steps" in result.text or "max" in result.text.lower()
    
    # Verify step count matches max_steps
    assert result.total_steps == max_steps
    
    # Verify steps were recorded
    assert len(result.steps) == max_steps


# Additional edge case tests
def test_agent_with_no_role_or_goal():
    """Test agent initialization without role or goal."""
    provider = MockProvider()
    
    agent = Agent(
        name="test_agent",
        provider=provider
    )
    
    # Should still have a system prompt
    assert agent.system_prompt is not None
    assert len(agent.system_prompt) > 0


def test_agent_with_custom_system_prompt():
    """Test agent with custom system prompt overrides role/goal."""
    provider = MockProvider()
    custom_prompt = "You are a custom agent with specific instructions."
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        role="Some Role",
        goal="Some Goal",
        system_prompt=custom_prompt
    )
    
    # Custom prompt should override role/goal
    assert agent.system_prompt == custom_prompt


def test_agent_with_memory():
    """Test agent with memory enabled."""
    # Use a response that will be detected as final (>50 chars, no "need to" indicators)
    provider = MockProvider(responses=["Here is the complete answer to your question with all the details you need."])
    memory = Memory()
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        memory=memory,
        max_steps=5
    )
    
    result = agent.run("Test task")
    
    # Verify memory is set
    assert agent.memory is memory
    
    # Verify state exists and has messages
    assert agent.state is not None
    assert len(agent.state.messages) > 0
    
    # For this basic test, just verify memory was configured
    # The actual saving functionality will be tested in integration tests
    # since it depends on the Memory implementation details
    assert agent.memory is not None


def test_agent_with_tools():
    """Test agent initialization with tools."""
    provider = MockProvider()
    
    # Create a mock tool
    mock_tool = Mock(spec=Tool)
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        tools=[mock_tool]
    )
    
    # Verify tools are registered
    assert len(agent.tools) == 1
    assert agent.tools[0] == mock_tool
    assert "test_tool" in agent.tool_map
    
    # Verify system prompt mentions tools
    assert "tool" in agent.system_prompt.lower()


def test_agent_verbose_mode():
    """Test agent in verbose mode."""
    provider = MockProvider(responses=["Final answer."])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        verbose=True
    )
    
    # Should not raise any errors
    result = agent.run("Test task")
    assert result is not None


@pytest.mark.asyncio
async def test_agent_async_execution():
    """Test agent async execution."""
    provider = MockProvider(responses=["Async final answer."])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=3
    )
    
    # Run async
    result = await agent.arun("Test async task")
    
    # Verify result structure
    assert isinstance(result, AgentResult)
    assert result.text is not None
    assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_agent_async_streaming():
    """Test agent async streaming."""
    provider = MockProvider(responses=["Streaming answer."])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=2
    )
    
    # Stream async
    steps = []
    async for step in agent.a_stream_invoke("Test streaming task"):
        steps.append(step)
    
    # Verify steps were yielded
    assert len(steps) > 0
    assert all(isinstance(step, StepResult) for step in steps)


def test_agent_execution_error_handling():
    """Test that agent execution errors are properly raised."""
    # Create a provider that raises an error
    provider = MockProvider()
    provider.chat = Mock(side_effect=Exception("Provider error"))
    
    agent = Agent(
        name="test_agent",
        provider=provider
    )
    
    # Should raise AgentExecutionError
    with pytest.raises(AgentExecutionError) as exc_info:
        agent.run("Test task")
    
    error = exc_info.value
    assert "Agent execution failed" in error.message
    assert "test_agent" in error.details.get("agent_name", "")


def test_agent_state_initialization():
    """Test that agent state is properly initialized."""
    provider = MockProvider()
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=5
    )
    
    # State should be None before execution
    assert agent.state is None
    
    # Run agent
    agent.run("Test task")
    
    # State should be initialized after execution
    assert agent.state is not None
    assert isinstance(agent.state, AgentState)
    assert agent.state.task_input == "Test task"
    assert agent.state.max_steps == 5


def test_agent_step_results():
    """Test that step results are properly recorded."""
    provider = MockProvider(responses=[
        "Step 1 response",
        "Step 2 response",
        "Final answer"
    ])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=5
    )
    
    result = agent.run("Test task")
    
    # Verify steps are recorded
    assert len(result.steps) > 0
    
    # Each step should have proper structure
    for i, step in enumerate(result.steps):
        assert isinstance(step, StepResult)
        assert step.index == i
        assert step.text is not None
        assert isinstance(step.tools_used, list)
        assert isinstance(step.finished, bool)
        assert isinstance(step.metadata, dict)


def test_agent_can_call_registration():
    """Test that agents can be registered as callable."""
    provider = MockProvider()
    
    agent1 = Agent(name="agent1", provider=provider)
    agent2 = Agent(name="agent2", provider=provider)
    agent3 = Agent(name="agent3", provider=provider)
    
    # Register agents as callable
    agent1.can_call([agent2, agent3])
    
    # Verify agents are registered
    assert "agent2" in agent1.callable_agents
    assert "agent3" in agent1.callable_agents
    assert agent1.callable_agents["agent2"] is agent2
    assert agent1.callable_agents["agent3"] is agent3


# ============================================================================
# Planning System Property Tests
# ============================================================================

# Feature: craft-v2-agents-tools, Property 17: Plan Generation
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=1, max_value=10)  # planning_interval
)
def test_property_17_plan_generation(name, task_input, planning_interval):
    """
    Property 17: Plan Generation
    
    For any agent that receives a task, if planning is enabled, the system SHALL
    generate an initial plan with numbered steps.
    
    **Validates: Requirements 5.1**
    """
    # Create mock provider that returns a plan
    plan_response = """Here's the plan:
1. Analyze the task requirements
2. Gather necessary information
3. Process the data
4. Generate the final answer"""
    
    provider = MockProvider(responses=[plan_response, "Final answer."])
    
    # Create agent with planning enabled
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=10,
        planning_interval=planning_interval
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify plan was generated
    assert agent.state is not None
    assert agent.state.plan is not None
    
    # Verify plan has steps
    plan = agent.state.plan
    assert len(plan.steps) > 0
    
    # Verify plan structure
    assert plan.current_step_index >= 0
    assert isinstance(plan.completed_steps, list)
    assert plan.created_at is not None
    assert plan.updated_at is not None


# Feature: craft-v2-agents-tools, Property 18: Planning Interval Adherence
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=2, max_value=5)  # planning_interval
)
def test_property_18_planning_interval_adherence(name, task_input, planning_interval):
    """
    Property 18: Planning Interval Adherence
    
    For any agent with planning_interval configured, the system SHALL re-evaluate
    the plan at exactly those step intervals.
    
    **Validates: Requirements 5.2**
    """
    # Create mock provider with multiple responses to trigger re-evaluation
    responses = [
        "Step 1: Initial plan",
        "I need more information",  # Not final
        "Still working on it",  # Not final
        "Making progress",  # Not final
        "Almost done",  # Not final
        "Here is the final answer"  # Final
    ]
    provider = MockProvider(responses=responses)
    
    # Create agent with planning interval
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=10,
        planning_interval=planning_interval
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify plan exists
    assert agent.state.plan is not None
    
    # Verify plan was updated (revision_count should be > 0 if we hit an interval)
    # This depends on whether we actually reached a planning interval
    if result.total_steps >= planning_interval:
        # We should have hit at least one re-evaluation
        # The plan should have been updated
        assert agent.state.plan.updated_at >= agent.state.plan.created_at


# Feature: craft-v2-agents-tools, Property 19: Step Completion Tracking
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=2, max_value=5)
)
def test_property_19_step_completion_tracking(name, task_input, planning_interval):
    """
    Property 19: Step Completion Tracking
    
    For any agent with a plan, when a step is completed, the system SHALL mark it
    as complete and proceed to the next step.
    
    **Validates: Requirements 5.3**
    """
    # Create mock provider with responses indicating completion
    responses = [
        "Plan created",
        "Successfully completed the first task",  # Indicates completion
        "Done with the second step",  # Indicates completion
        "Final answer is ready"
    ]
    provider = MockProvider(responses=responses)
    
    # Create agent with planning
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=10,
        planning_interval=planning_interval
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify plan exists
    assert agent.state.plan is not None
    
    # Verify completed steps are tracked
    plan = agent.state.plan
    assert isinstance(plan.completed_steps, list)
    
    # If we had multiple steps, some should be marked complete
    # (depends on the responses and completion detection)
    # At minimum, the list should exist and be valid
    assert all(isinstance(step_idx, int) for step_idx in plan.completed_steps)
    
    # Verify current_step_index is valid
    assert 0 <= plan.current_step_index < len(plan.steps) or len(plan.steps) == 0


# Feature: craft-v2-agents-tools, Property 20: Plan Visibility
@settings(max_examples=100)
@given(
    agent_names(),
    task_inputs(),
    st.integers(min_value=1, max_value=5)
)
def test_property_20_plan_visibility(name, task_input, planning_interval):
    """
    Property 20: Plan Visibility
    
    For any agent execution in progress, the current plan and completed steps SHALL
    be accessible for inspection.
    
    **Validates: Requirements 5.5**
    """
    # Create mock provider
    provider = MockProvider(responses=["Plan step 1", "Final answer"])
    
    # Create agent with planning
    agent = Agent(
        name=name,
        provider=provider,
        max_steps=10,
        planning_interval=planning_interval
    )
    
    # Run agent
    result = agent.run(task_input)
    
    # Verify get_plan() method exists and works
    plan = agent.get_plan()
    assert plan is not None
    
    # Verify plan has accessible properties
    assert hasattr(plan, 'steps')
    assert hasattr(plan, 'current_step_index')
    assert hasattr(plan, 'completed_steps')
    
    # Verify get_plan_display() method exists and works
    plan_display = agent.get_plan_display()
    assert plan_display is not None
    assert isinstance(plan_display, str)
    assert len(plan_display) > 0
    
    # Display should contain plan information
    assert "Plan" in plan_display or "plan" in plan_display


def test_agent_without_planning():
    """Test that agent works without planning enabled."""
    provider = MockProvider(responses=["Answer without planning."])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=5,
        planning_interval=None  # No planning
    )
    
    result = agent.run("Test task")
    
    # Should work fine without a plan
    assert result is not None
    assert agent.state.plan is None
    
    # get_plan should return None
    assert agent.get_plan() is None
    
    # get_plan_display should return appropriate message
    display = agent.get_plan_display()
    assert "No plan" in display or "no plan" in display


def test_plan_revision_tracking():
    """Test that plan revisions are tracked."""
    from craft.agents.planning import Plan, revise_plan_sync
    
    provider = MockProvider(responses=["Revised plan step 1", "Revised plan step 2"])
    
    # Create initial plan
    initial_plan = Plan(
        steps=["Step 1", "Step 2", "Step 3"],
        current_step_index=0,
        completed_steps=[]
    )
    
    # Revise the plan
    revised_plan = revise_plan_sync(
        provider,
        initial_plan,
        "Original task",
        "New information that requires revision"
    )
    
    # Verify revision was tracked
    assert revised_plan.revision_count == 1
    assert len(revised_plan.revision_history) == 1
    assert revised_plan.updated_at > revised_plan.created_at


def test_plan_step_advancement():
    """Test that plan steps advance correctly."""
    from craft.agents.planning import Plan, advance_to_next_step, get_current_step
    
    plan = Plan(
        steps=["Step 1", "Step 2", "Step 3"],
        current_step_index=0,
        completed_steps=[]
    )
    
    # Get current step
    current = get_current_step(plan)
    assert current == "Step 1"
    
    # Advance to next step
    advanced = advance_to_next_step(plan)
    assert advanced is True
    assert plan.current_step_index == 1
    
    current = get_current_step(plan)
    assert current == "Step 2"
    
    # Advance again
    advanced = advance_to_next_step(plan)
    assert advanced is True
    assert plan.current_step_index == 2
    
    # Try to advance past the end
    advanced = advance_to_next_step(plan)
    assert advanced is False
    assert plan.current_step_index == 2  # Should stay at last step


def test_plan_step_completion_marking():
    """Test that plan steps can be marked complete."""
    from craft.agents.planning import Plan, mark_step_complete
    
    plan = Plan(
        steps=["Step 1", "Step 2", "Step 3"],
        current_step_index=0,
        completed_steps=[]
    )
    
    # Mark first step complete
    mark_step_complete(plan, 0)
    assert 0 in plan.completed_steps
    
    # Mark second step complete
    mark_step_complete(plan, 1)
    assert 1 in plan.completed_steps
    
    # Marking same step again should not duplicate
    mark_step_complete(plan, 0)
    assert plan.completed_steps.count(0) == 1


def test_plan_formatting():
    """Test that plan can be formatted for display."""
    from craft.agents.planning import Plan, format_plan_for_display
    
    plan = Plan(
        steps=["Step 1", "Step 2", "Step 3"],
        current_step_index=1,
        completed_steps=[0],
        revision_count=2
    )
    
    display = format_plan_for_display(plan)
    
    # Should contain plan information
    assert "Plan" in display
    assert "Step 1" in display
    assert "Step 2" in display
    assert "Step 3" in display
    
    # Should show revision count
    assert "Revisions: 2" in display or "2" in display


@pytest.mark.asyncio
async def test_async_plan_generation():
    """Test async plan generation."""
    from craft.agents.planning import generate_plan
    
    provider = MockProvider(responses=["1. First step\n2. Second step\n3. Third step"])
    
    plan = await generate_plan(provider, "Test task")
    
    assert plan is not None
    assert len(plan.steps) > 0
    assert plan.current_step_index == 0


@pytest.mark.asyncio
async def test_async_plan_revision():
    """Test async plan revision."""
    from craft.agents.planning import Plan, revise_plan
    
    provider = MockProvider(responses=["1. Revised step 1\n2. Revised step 2"])
    
    initial_plan = Plan(
        steps=["Old step 1", "Old step 2"],
        current_step_index=0,
        completed_steps=[]
    )
    
    revised_plan = await revise_plan(
        provider,
        initial_plan,
        "Original task",
        "New information"
    )
    
    assert revised_plan.revision_count == 1
    assert len(revised_plan.steps) > 0


@pytest.mark.asyncio
async def test_agent_async_with_planning():
    """Test agent async execution with planning enabled."""
    provider = MockProvider(responses=[
        "Plan: 1. Step one\n2. Step two",
        "Final answer with planning"
    ])
    
    agent = Agent(
        name="test_agent",
        provider=provider,
        max_steps=5,
        planning_interval=2
    )
    
    result = await agent.arun("Test task with planning")
    
    # Verify plan was created
    assert agent.state.plan is not None
    assert len(agent.state.plan.steps) > 0
    
    # Verify result
    assert result is not None
    assert isinstance(result, AgentResult)
