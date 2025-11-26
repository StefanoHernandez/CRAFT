"""Core agent implementation for autonomous task execution."""

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import time

from craft.providers.base import Provider, Message, Role, ChatResponse
from craft.tools.base import Tool
from craft.core.memory import Memory
from craft.core.errors import AgentExecutionError, ToolExecutionError
from craft.agents.planning import (
    Plan,
    generate_plan,
    generate_plan_sync,
    revise_plan,
    revise_plan_sync,
    mark_step_complete,
    advance_to_next_step,
    get_current_step,
    format_plan_for_display,
)


class ToolCall(BaseModel):
    """Record of a tool invocation."""

    tool_name: str
    arguments: Dict[str, Any]
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Plan is now imported from craft.agents.planning


class AgentState(BaseModel):
    """State maintained during agent execution."""

    task_input: str
    current_step: int = 0
    max_steps: int
    messages: List[Message] = Field(default_factory=list)
    tools_used: List[ToolCall] = Field(default_factory=list)
    plan: Optional[Plan] = None
    finished: bool = False
    result: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StepResult(BaseModel):
    """Result of a single agent execution step."""

    index: int
    text: str
    tools_used: List[ToolCall] = Field(default_factory=list)
    finished: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentResult(BaseModel):
    """Final result from agent execution."""

    text: str
    steps: List[StepResult] = Field(default_factory=list)
    total_steps: int
    tools_used: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentConfig(BaseModel):
    """Configuration for an Agent."""

    name: str
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    max_steps: int = Field(default=10, ge=1, le=100)
    planning_interval: Optional[int] = Field(default=None, ge=1)
    terminate_on_text: bool = True
    verbose: bool = False


class Agent:
    """
    Autonomous agent that can reason and execute multi-step tasks.

    Inspired by DataPizza AI's simplicity and CrewAI's role-based design.
    The agent can use tools, maintain conversation history, and execute
    complex tasks through iterative reasoning.

    Example:
        from craft.agents import Agent
        from craft.providers import AnthropicProvider
        from craft.tools.builtin import search_web

        provider = AnthropicProvider(api_key="...", model="claude-3-sonnet")
        agent = Agent(
            name="research_agent",
            provider=provider,
            role="Research Assistant",
            goal="Find and summarize information",
            tools=[search_web]
        )

        result = agent.run("What are the latest developments in AI?")
        print(result.text)
    """

    def __init__(
        self,
        name: str,
        provider: Provider,
        role: Optional[str] = None,
        goal: Optional[str] = None,
        backstory: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        max_steps: int = 10,
        planning_interval: Optional[int] = None,
        memory: Optional[Union[bool, Memory]] = None,
        verbose: bool = False,
    ):
        """
        Initialize agent with configuration.

        Args:
            name: Agent name/identifier
            provider: LLM provider for agent reasoning
            role: Agent's role (e.g., "Research Assistant")
            goal: Agent's goal (e.g., "Find accurate information")
            backstory: Agent's backstory for context
            system_prompt: Custom system prompt (overrides role/goal/backstory)
            tools: List of tools available to the agent
            max_steps: Maximum execution steps before termination
            planning_interval: Steps between plan re-evaluations (None = no planning)
            memory: Memory instance or True for default memory, False/None for no memory
            verbose: Whether to print execution details
        """
        self.config = AgentConfig(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            system_prompt=system_prompt,
            max_steps=max_steps,
            planning_interval=planning_interval,
            verbose=verbose,
        )

        self.provider = provider
        self.tools = tools or []
        self.tool_map = {tool.name: tool for tool in self.tools}

        # Set up memory
        if memory is True:
            self.memory = Memory()
        elif isinstance(memory, Memory):
            self.memory = memory
        else:
            self.memory = None

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

        # State for current execution
        self.state: Optional[AgentState] = None

        # Track callable agents (for multi-agent collaboration)
        self.callable_agents: Dict[str, "Agent"] = {}
        
        # Track agent call hierarchy to prevent infinite recursion
        self._call_stack: List[str] = []
        
        # Track aggregated results from multi-agent collaboration
        self._aggregated_results: Dict[str, Any] = {
            'agent_calls': [],
            'total_steps': 0,
            'total_tools_used': set(),
            'total_execution_time': 0.0,
        }

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def role(self) -> Optional[str]:
        """Get agent role."""
        return self.config.role

    @property
    def goal(self) -> Optional[str]:
        """Get agent goal."""
        return self.config.goal

    @property
    def backstory(self) -> Optional[str]:
        """Get agent backstory."""
        return self.config.backstory

    def _build_system_prompt(self) -> str:
        """
        Build system prompt from role, goal, and backstory.

        Returns:
            System prompt string
        """
        if self.config.system_prompt:
            return self.config.system_prompt

        prompt_parts = []

        if self.config.role:
            prompt_parts.append(f"You are a {self.config.role}.")

        if self.config.goal:
            prompt_parts.append(f"Your goal is: {self.config.goal}")

        if self.config.backstory:
            prompt_parts.append(f"Background: {self.config.backstory}")

        if self.tools:
            tool_names = ", ".join(tool.name for tool in self.tools)
            prompt_parts.append(
                f"\nYou have access to the following tools: {tool_names}"
            )
            prompt_parts.append(
                "Use tools when needed to accomplish your task. "
                "When you have enough information to answer, provide your final answer."
            )

        if not prompt_parts:
            prompt_parts.append(
                "You are a helpful AI assistant. Answer questions accurately and concisely."
            )

        return "\n\n".join(prompt_parts)

    def run(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> AgentResult:
        """
        Execute task and return final result.

        Args:
            task_input: Task description or question
            tool_choice: Tool usage control - "auto", "required", "required_first", "none", or list of tool names
            **kwargs: Additional provider parameters

        Returns:
            AgentResult with final answer and execution metadata

        Raises:
            AgentExecutionError: If execution fails
        """
        # Initialize execution state
        self._initialize_state(task_input)
        
        # Reset aggregated results for new execution
        self._reset_aggregated_results()

        # Track execution metadata
        start_time = time.time()
        step_results: List[StepResult] = []

        try:
            # Main execution loop
            while not self.state.finished and self.state.current_step < self.state.max_steps:
                if self.config.verbose:
                    print(f"\n--- Step {self.state.current_step + 1} ---")

                # Check if we should re-evaluate the plan
                if self._should_reevaluate_plan():
                    self._reevaluate_plan()

                # Execute one step
                step_result = self._execute_step(tool_choice, **kwargs)
                step_results.append(step_result)

                # Check if finished
                if step_result.finished:
                    self.state.finished = True
                    self.state.result = step_result.text
                    break

                self.state.current_step += 1

            # Calculate execution time
            execution_time = time.time() - start_time

            # Handle max steps termination
            if not self.state.finished:
                result = self._handle_max_steps(step_results, execution_time)
                # Save to memory even for partial results
                if self.memory:
                    self._save_to_memory()
                return result

            # Build final result
            tools_used_names = list(set(tc.tool_name for tc in self.state.tools_used))

            # Include aggregated results from multi-agent collaboration
            metadata = {
                "execution_time_seconds": execution_time,
                "max_steps_reached": False,
            }
            
            # Add aggregated results if any agent calls were made
            aggregated = self.get_aggregated_results()
            if aggregated['agent_calls']:
                metadata['multi_agent_collaboration'] = aggregated

            result = AgentResult(
                text=self.state.result or "",
                steps=step_results,
                total_steps=self.state.current_step + 1,
                tools_used=tools_used_names,
                metadata=metadata,
            )

            # Save to memory if enabled
            if self.memory:
                self._save_to_memory()

            return result

        except Exception as e:
            raise AgentExecutionError(
                f"Agent execution failed: {str(e)}",
                details={
                    "agent_name": self.config.name,
                    "current_step": self.state.current_step,
                    "task_input": task_input,
                },
            )

    def _initialize_state(self, task_input: str) -> None:
        """
        Initialize agent state for new execution.

        Args:
            task_input: Task description
        """
        # Create initial messages with system prompt
        messages = [
            Message(role=Role.SYSTEM, content=self.system_prompt),
            Message(role=Role.USER, content=task_input),
        ]

        # Generate initial plan if planning is enabled
        plan = None
        if self.config.planning_interval is not None:
            if self.config.verbose:
                print("Generating initial plan...")
            plan = generate_plan_sync(self.provider, task_input)
            if self.config.verbose:
                print(format_plan_for_display(plan))

        self.state = AgentState(
            task_input=task_input,
            current_step=0,
            max_steps=self.config.max_steps,
            messages=messages,
            tools_used=[],
            plan=plan,
            finished=False,
        )

    def _execute_step(
        self, tool_choice: Union[str, List[str]], **kwargs: Any
    ) -> StepResult:
        """
        Execute a single reasoning/action step.

        Args:
            tool_choice: Tool usage control
            **kwargs: Provider parameters

        Returns:
            StepResult for this step
        """
        # If we have a plan, include current step in context
        if self.state.plan:
            current_step_text = get_current_step(self.state.plan)
            if current_step_text and self.config.verbose:
                print(f"Current plan step: {current_step_text}")

        # Call provider to get next action
        response = self.provider.chat(
            messages=self.state.messages,
            stream=False,
            **kwargs,
        )

        # Extract response content
        response_text = response.content if isinstance(response, ChatResponse) else str(response)

        # Add assistant response to messages
        self.state.messages.append(
            Message(role=Role.ASSISTANT, content=response_text)
        )

        # Check if this is a final answer (no tool calls)
        # For now, we'll use a simple heuristic - if response doesn't mention tools
        # and seems conclusive, mark as finished
        is_finished = self._is_final_answer(response_text)

        # Track step completion in plan
        if self.state.plan and not is_finished:
            # Check if step appears complete based on response
            if self._is_step_complete(response_text):
                mark_step_complete(self.state.plan, self.state.plan.current_step_index)
                advance_to_next_step(self.state.plan)
                if self.config.verbose:
                    print(f"✓ Completed plan step {self.state.plan.current_step_index}")

        step_result = StepResult(
            index=self.state.current_step,
            text=response_text,
            tools_used=[],
            finished=is_finished,
            metadata={},
        )

        if self.config.verbose:
            print(f"Response: {response_text[:200]}...")
            if is_finished:
                print("✓ Final answer detected")

        return step_result

    def _is_final_answer(self, text: str) -> bool:
        """
        Determine if response is a final answer.

        Args:
            text: Response text

        Returns:
            True if this appears to be a final answer
        """
        # Simple heuristic: if text doesn't mention needing more info or tools
        # and has substantial content, consider it final
        text_lower = text.lower()

        # Indicators that it's NOT final
        not_final_indicators = [
            "i need to",
            "let me search",
            "i'll look up",
            "i should check",
            "i don't have enough information",
        ]

        for indicator in not_final_indicators:
            if indicator in text_lower:
                return False

        # If we have substantial content (>50 chars), consider it final
        return len(text.strip()) > 50

    def _is_step_complete(self, response_text: str) -> bool:
        """
        Determine if a plan step is complete based on response.

        Args:
            response_text: Agent's response

        Returns:
            True if step appears complete
        """
        text_lower = response_text.lower()

        # Indicators of completion
        completion_indicators = [
            "completed",
            "done",
            "finished",
            "successfully",
            "found",
            "retrieved",
            "obtained",
        ]

        for indicator in completion_indicators:
            if indicator in text_lower:
                return True

        # If response is substantial and doesn't indicate more work needed
        if len(response_text.strip()) > 100:
            not_complete_indicators = [
                "i need to",
                "next i will",
                "i should",
                "let me",
            ]
            for indicator in not_complete_indicators:
                if indicator in text_lower:
                    return False
            return True

        return False

    def _should_reevaluate_plan(self) -> bool:
        """
        Check if plan should be re-evaluated at this step.

        Returns:
            True if plan should be re-evaluated
        """
        if not self.state.plan or self.config.planning_interval is None:
            return False

        # Re-evaluate at planning intervals
        return (self.state.current_step > 0 and 
                self.state.current_step % self.config.planning_interval == 0)

    def _reevaluate_plan(self) -> None:
        """Re-evaluate and potentially revise the current plan."""
        if not self.state.plan:
            return

        # Gather context from recent steps
        recent_context = self._gather_recent_context()

        if self.config.verbose:
            print(f"\n--- Re-evaluating plan at step {self.state.current_step} ---")

        # Revise plan based on new information
        self.state.plan = revise_plan_sync(
            self.provider,
            self.state.plan,
            self.state.task_input,
            recent_context,
        )

        if self.config.verbose:
            print(format_plan_for_display(self.state.plan))

    def _gather_recent_context(self) -> str:
        """
        Gather context from recent execution for plan revision.

        Returns:
            Context string summarizing recent progress
        """
        # Get last few messages
        recent_messages = self.state.messages[-5:] if len(self.state.messages) > 5 else self.state.messages

        context_parts = [f"Current step: {self.state.current_step}"]

        # Add recent conversation
        for msg in recent_messages:
            if msg.role == Role.ASSISTANT:
                context_parts.append(f"Agent: {msg.content[:200]}...")

        # Add tools used
        if self.state.tools_used:
            recent_tools = [tc.tool_name for tc in self.state.tools_used[-3:]]
            context_parts.append(f"Recent tools used: {', '.join(recent_tools)}")

        return "\n".join(context_parts)

    async def _areevaluate_plan(self) -> None:
        """Async version of _reevaluate_plan."""
        if not self.state.plan:
            return

        # Gather context from recent steps
        recent_context = self._gather_recent_context()

        if self.config.verbose:
            print(f"\n--- Re-evaluating plan at step {self.state.current_step} ---")

        # Revise plan based on new information
        self.state.plan = await revise_plan(
            self.provider,
            self.state.plan,
            self.state.task_input,
            recent_context,
        )

        if self.config.verbose:
            print(format_plan_for_display(self.state.plan))

    def _handle_max_steps(self, step_results: List[StepResult], execution_time: float = 0.0) -> AgentResult:
        """
        Handle graceful termination when max_steps is reached.

        Args:
            step_results: Results from all steps
            execution_time: Execution time in seconds

        Returns:
            AgentResult with partial results and explanation
        """
        # Get the last response as partial result
        last_text = step_results[-1].text if step_results else "No results generated"

        partial_result = (
            f"Task incomplete: Maximum steps ({self.config.max_steps}) reached.\n\n"
            f"Partial result:\n{last_text}"
        )

        tools_used_names = list(set(tc.tool_name for tc in self.state.tools_used))

        return AgentResult(
            text=partial_result,
            steps=step_results,
            total_steps=self.state.current_step,
            tools_used=tools_used_names,
            metadata={
                "execution_time_seconds": execution_time,
                "max_steps_reached": True,
                "terminated": "max_steps",
                "partial": True,
            },
        )

    def _save_to_memory(self) -> None:
        """Save current execution to memory."""
        if not self.memory or not self.state:
            return

        # Create a conversation from the current state
        from craft.core.conversation import Conversation

        conversation = Conversation(id=f"{self.config.name}_{int(time.time())}")
        conversation.messages = self.state.messages

        self.memory.save(conversation)

    def stream_invoke(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Iterator[StepResult]:
        """
        Stream execution steps in real-time.

        Args:
            task_input: Task description
            tool_choice: Tool usage control
            **kwargs: Provider parameters

        Yields:
            StepResult objects for each execution step
        """
        # Initialize execution state
        self._initialize_state(task_input)

        # Track execution metadata
        start_time = time.time()

        try:
            # Main execution loop - yield after each step
            while not self.state.finished and self.state.current_step < self.state.max_steps:
                if self.config.verbose:
                    print(f"\n--- Step {self.state.current_step + 1} ---")

                # Check if we should re-evaluate the plan
                if self._should_reevaluate_plan():
                    self._reevaluate_plan()

                # Execute one step
                step_result = self._execute_step(tool_choice, **kwargs)
                
                # Yield the step result immediately
                yield step_result

                # Check if finished
                if step_result.finished:
                    self.state.finished = True
                    self.state.result = step_result.text
                    break

                self.state.current_step += 1

            # Calculate execution time
            execution_time = time.time() - start_time

            # Handle max steps termination - yield final result
            if not self.state.finished:
                # Create a final step result indicating max steps reached
                partial_text = (
                    f"Task incomplete: Maximum steps ({self.config.max_steps}) reached.\n\n"
                    f"Partial result:\n{step_result.text if 'step_result' in locals() else 'No results generated'}"
                )
                
                final_step = StepResult(
                    index=self.state.current_step,
                    text=partial_text,
                    tools_used=[],
                    finished=True,
                    metadata={
                        "execution_time_seconds": execution_time,
                        "max_steps_reached": True,
                        "terminated": "max_steps",
                        "partial": True,
                    },
                )
                yield final_step

            # Save to memory if enabled
            if self.memory:
                self._save_to_memory()

        except Exception as e:
            # Yield error as final step
            error_step = StepResult(
                index=self.state.current_step if self.state else 0,
                text=f"Error: {str(e)}",
                tools_used=[],
                finished=True,
                metadata={"error": True, "error_message": str(e)},
            )
            yield error_step
            
            raise AgentExecutionError(
                f"Agent execution failed: {str(e)}",
                details={
                    "agent_name": self.config.name,
                    "current_step": self.state.current_step if self.state else 0,
                    "task_input": task_input,
                },
            )

    async def _ainitialize_state(self, task_input: str) -> None:
        """
        Async version of _initialize_state.

        Args:
            task_input: Task description
        """
        # Create initial messages with system prompt
        messages = [
            Message(role=Role.SYSTEM, content=self.system_prompt),
            Message(role=Role.USER, content=task_input),
        ]

        # Generate initial plan if planning is enabled
        plan = None
        if self.config.planning_interval is not None:
            if self.config.verbose:
                print("Generating initial plan...")
            plan = await generate_plan(self.provider, task_input)
            if self.config.verbose:
                print(format_plan_for_display(plan))

        self.state = AgentState(
            task_input=task_input,
            current_step=0,
            max_steps=self.config.max_steps,
            messages=messages,
            tools_used=[],
            plan=plan,
            finished=False,
        )

    async def arun(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> AgentResult:
        """
        Async version of run.

        Args:
            task_input: Task description
            tool_choice: Tool usage control
            **kwargs: Provider parameters

        Returns:
            AgentResult with final answer and execution metadata
        """
        # Initialize execution state
        await self._ainitialize_state(task_input)
        
        # Reset aggregated results for new execution
        self._reset_aggregated_results()

        # Track execution metadata
        start_time = time.time()
        step_results: List[StepResult] = []

        try:
            # Main execution loop
            while not self.state.finished and self.state.current_step < self.state.max_steps:
                if self.config.verbose:
                    print(f"\n--- Step {self.state.current_step + 1} ---")

                # Check if we should re-evaluate the plan
                if self._should_reevaluate_plan():
                    await self._areevaluate_plan()

                # Execute one step asynchronously
                step_result = await self._aexecute_step(tool_choice, **kwargs)
                step_results.append(step_result)

                # Check if finished
                if step_result.finished:
                    self.state.finished = True
                    self.state.result = step_result.text
                    break

                self.state.current_step += 1

            # Calculate execution time
            execution_time = time.time() - start_time

            # Handle max steps termination
            if not self.state.finished:
                result = self._handle_max_steps(step_results, execution_time)
                # Save to memory even for partial results
                if self.memory:
                    self._save_to_memory()
                return result

            # Build final result
            tools_used_names = list(set(tc.tool_name for tc in self.state.tools_used))

            # Include aggregated results from multi-agent collaboration
            metadata = {
                "execution_time_seconds": execution_time,
                "max_steps_reached": False,
            }
            
            # Add aggregated results if any agent calls were made
            aggregated = self.get_aggregated_results()
            if aggregated['agent_calls']:
                metadata['multi_agent_collaboration'] = aggregated

            result = AgentResult(
                text=self.state.result or "",
                steps=step_results,
                total_steps=self.state.current_step + 1,
                tools_used=tools_used_names,
                metadata=metadata,
            )

            # Save to memory if enabled
            if self.memory:
                self._save_to_memory()

            return result

        except Exception as e:
            raise AgentExecutionError(
                f"Agent execution failed: {str(e)}",
                details={
                    "agent_name": self.config.name,
                    "current_step": self.state.current_step,
                    "task_input": task_input,
                },
            )

    async def _aexecute_step(
        self, tool_choice: Union[str, List[str]], **kwargs: Any
    ) -> StepResult:
        """
        Execute a single reasoning/action step asynchronously.

        Args:
            tool_choice: Tool usage control
            **kwargs: Provider parameters

        Returns:
            StepResult for this step
        """
        # If we have a plan, include current step in context
        if self.state.plan:
            current_step_text = get_current_step(self.state.plan)
            if current_step_text and self.config.verbose:
                print(f"Current plan step: {current_step_text}")

        # Call provider asynchronously
        response = await self.provider.achat(
            messages=self.state.messages,
            stream=False,
            **kwargs,
        )

        # Extract response content
        response_text = response.content if isinstance(response, ChatResponse) else str(response)

        # Add assistant response to messages
        self.state.messages.append(
            Message(role=Role.ASSISTANT, content=response_text)
        )

        # Check if this is a final answer
        is_finished = self._is_final_answer(response_text)

        # Track step completion in plan
        if self.state.plan and not is_finished:
            # Check if step appears complete based on response
            if self._is_step_complete(response_text):
                mark_step_complete(self.state.plan, self.state.plan.current_step_index)
                advance_to_next_step(self.state.plan)
                if self.config.verbose:
                    print(f"✓ Completed plan step {self.state.plan.current_step_index}")

        step_result = StepResult(
            index=self.state.current_step,
            text=response_text,
            tools_used=[],
            finished=is_finished,
            metadata={},
        )

        if self.config.verbose:
            print(f"Response: {response_text[:200]}...")
            if is_finished:
                print("✓ Final answer detected")

        return step_result

    async def a_stream_invoke(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> AsyncIterator[StepResult]:
        """
        Async version of stream_invoke.

        Args:
            task_input: Task description
            tool_choice: Tool usage control
            **kwargs: Provider parameters

        Yields:
            StepResult objects for each execution step
        """
        # Initialize execution state
        await self._ainitialize_state(task_input)

        # Track execution metadata
        start_time = time.time()

        try:
            # Main execution loop - yield after each step
            while not self.state.finished and self.state.current_step < self.state.max_steps:
                if self.config.verbose:
                    print(f"\n--- Step {self.state.current_step + 1} ---")

                # Check if we should re-evaluate the plan
                if self._should_reevaluate_plan():
                    await self._areevaluate_plan()

                # Execute one step asynchronously
                step_result = await self._aexecute_step(tool_choice, **kwargs)
                
                # Yield the step result immediately
                yield step_result

                # Check if finished
                if step_result.finished:
                    self.state.finished = True
                    self.state.result = step_result.text
                    break

                self.state.current_step += 1

            # Calculate execution time
            execution_time = time.time() - start_time

            # Handle max steps termination - yield final result
            if not self.state.finished:
                # Create a final step result indicating max steps reached
                partial_text = (
                    f"Task incomplete: Maximum steps ({self.config.max_steps}) reached.\n\n"
                    f"Partial result:\n{step_result.text if 'step_result' in locals() else 'No results generated'}"
                )
                
                final_step = StepResult(
                    index=self.state.current_step,
                    text=partial_text,
                    tools_used=[],
                    finished=True,
                    metadata={
                        "execution_time_seconds": execution_time,
                        "max_steps_reached": True,
                        "terminated": "max_steps",
                        "partial": True,
                    },
                )
                yield final_step

            # Save to memory if enabled
            if self.memory:
                self._save_to_memory()

        except Exception as e:
            # Yield error as final step
            error_step = StepResult(
                index=self.state.current_step if self.state else 0,
                text=f"Error: {str(e)}",
                tools_used=[],
                finished=True,
                metadata={"error": True, "error_message": str(e)},
            )
            yield error_step
            
            raise AgentExecutionError(
                f"Agent execution failed: {str(e)}",
                details={
                    "agent_name": self.config.name,
                    "current_step": self.state.current_step if self.state else 0,
                    "task_input": task_input,
                },
            )

    def can_call(self, agents: List["Agent"]) -> None:
        """
        Register other agents as callable tools.

        This allows the current agent to call other agents as if they were tools,
        enabling multi-agent collaboration. Each agent is wrapped as a tool with
        its name, role, and goal as metadata.

        Args:
            agents: List of agents to make callable

        Example:
            researcher = Agent(name="researcher", provider=provider, role="Researcher")
            writer = Agent(name="writer", provider=provider, role="Writer")
            coordinator = Agent(name="coordinator", provider=provider)
            
            coordinator.can_call([researcher, writer])
            # Now coordinator can call researcher and writer as tools
        """
        from craft.tools.base import Tool, ToolMetadata, ToolParameter
        
        for agent in agents:
            # Store agent reference
            self.callable_agents[agent.config.name] = agent

            # Create a tool wrapper for the agent
            agent_tool = self._create_agent_tool(agent)
            
            # Add to tools list and tool map
            self.tools.append(agent_tool)
            self.tool_map[agent_tool.name] = agent_tool
            
            # Rebuild system prompt to include new tool
            self.system_prompt = self._build_system_prompt()

    def delegate_to(self, agents_map: Dict[str, "Agent"]) -> None:
        """
        Register agents with custom names for delegation.
        
        This is a convenience method similar to can_call() but allows
        specifying custom tool names for agent delegation. Useful for
        more descriptive delegation patterns.
        
        Args:
            agents_map: Dictionary mapping tool names to Agent instances
        
        Example:
            weather_agent = Agent(name="weather", provider=provider)
            research_agent = Agent(name="research", provider=provider)
            
            coordinator.delegate_to({
                "get_weather_forecast": weather_agent,
                "search_information": research_agent
            })
            # Now coordinator can use more descriptive tool names
        """
        from craft.tools.base import Tool, ToolMetadata, ToolParameter
        
        for tool_name, agent in agents_map.items():
            # Store agent reference with custom name
            self.callable_agents[tool_name] = agent
            
            # Create a tool wrapper with custom name
            agent_tool = self._create_agent_tool_with_name(agent, tool_name)
            
            # Add to tools list and tool map
            self.tools.append(agent_tool)
            self.tool_map[agent_tool.name] = agent_tool
        
        # Rebuild system prompt to include new tools
        self.system_prompt = self._build_system_prompt()

    def _create_agent_tool_with_name(self, agent: "Agent", tool_name: str) -> "Tool":
        """
        Create a tool wrapper for an agent with a custom name.
        
        Args:
            agent: Agent to wrap as a tool
            tool_name: Custom name for the tool
        
        Returns:
            Tool instance that calls the agent
        """
        from craft.tools.base import Tool, ToolMetadata, ToolParameter
        
        # Build description from agent's role and goal
        description_parts = [f"Delegate to {agent.config.name}"]
        if agent.config.role:
            description_parts.append(f"(Role: {agent.config.role})")
        if agent.config.goal:
            description_parts.append(f"to {agent.config.goal}")
        
        description = " ".join(description_parts)
        
        # Create metadata with custom tool name
        metadata = ToolMetadata(
            name=tool_name,
            description=description,
            parameters=[
                ToolParameter(
                    name="task",
                    type="str",
                    description="The task or question to give to the agent",
                    required=True,
                )
            ],
            return_type="str",
            json_schema={
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "The task or question to give to the agent",
                            }
                        },
                        "required": ["task"],
                    },
                },
            },
        )
        
        # Create wrapper function (reuse same logic as _create_agent_tool)
        def agent_wrapper(task: str) -> str:
            """Execute the agent with the given task."""
            if not hasattr(self, '_call_stack'):
                self._call_stack = []
            
            if not hasattr(self, '_aggregated_results'):
                self._aggregated_results = {
                    'agent_calls': [],
                    'total_steps': 0,
                    'total_tools_used': set(),
                    'total_execution_time': 0.0,
                }
            
            if agent.config.name in self._call_stack:
                raise AgentExecutionError(
                    f"Circular agent call detected: {' -> '.join(self._call_stack)} -> {agent.config.name}",
                    details={
                        "call_stack": self._call_stack,
                        "attempted_agent": agent.config.name,
                    }
                )
            
            self._call_stack.append(agent.config.name)
            
            try:
                result = agent.run(task)
                
                self._aggregated_results['agent_calls'].append({
                    'agent_name': agent.config.name,
                    'delegated_as': tool_name,  # Track custom name
                    'task': task,
                    'result': result.text,
                    'steps': result.total_steps,
                    'tools_used': result.tools_used,
                    'metadata': result.metadata,
                })
                
                self._aggregated_results['total_steps'] += result.total_steps
                self._aggregated_results['total_tools_used'].update(result.tools_used)
                self._aggregated_results['total_execution_time'] += result.metadata.get('execution_time_seconds', 0.0)
                
                return result.text
            finally:
                self._call_stack.pop()
        
        return Tool(
            name=tool_name,
            description=description,
            func=agent_wrapper,
            metadata=metadata,
        )

    def _create_agent_tool(self, agent: "Agent") -> "Tool":
        """
        Create a tool wrapper for an agent.

        Args:
            agent: Agent to wrap as a tool

        Returns:
            Tool instance that calls the agent
        """
        from craft.tools.base import Tool, ToolMetadata, ToolParameter
        
        # Build description from agent's role and goal
        description_parts = [f"Call the {agent.config.name} agent"]
        if agent.config.role:
            description_parts.append(f"(Role: {agent.config.role})")
        if agent.config.goal:
            description_parts.append(f"to {agent.config.goal}")
        
        description = " ".join(description_parts)
        
        # Create metadata for the agent tool
        metadata = ToolMetadata(
            name=agent.config.name,
            description=description,
            parameters=[
                ToolParameter(
                    name="task",
                    type="str",
                    description="The task or question to give to the agent",
                    required=True,
                )
            ],
            return_type="str",
            json_schema={
                "type": "function",
                "function": {
                    "name": agent.config.name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "The task or question to give to the agent",
                            }
                        },
                        "required": ["task"],
                    },
                },
            },
        )
        
        # Create wrapper function that calls the agent
        def agent_wrapper(task: str) -> str:
            """Execute the agent with the given task."""
            # Track call hierarchy to prevent recursion
            if not hasattr(self, '_call_stack'):
                self._call_stack = []
            
            # Initialize aggregated results tracking if not exists
            if not hasattr(self, '_aggregated_results'):
                self._aggregated_results = {
                    'agent_calls': [],
                    'total_steps': 0,
                    'total_tools_used': set(),
                    'total_execution_time': 0.0,
                }
            
            # Check for circular calls
            if agent.config.name in self._call_stack:
                raise AgentExecutionError(
                    f"Circular agent call detected: {' -> '.join(self._call_stack)} -> {agent.config.name}",
                    details={
                        "call_stack": self._call_stack,
                        "attempted_agent": agent.config.name,
                    }
                )
            
            # Add to call stack
            self._call_stack.append(agent.config.name)
            
            try:
                # Execute the agent
                result = agent.run(task)
                
                # Aggregate results from the called agent
                self._aggregated_results['agent_calls'].append({
                    'agent_name': agent.config.name,
                    'task': task,
                    'result': result.text,
                    'steps': result.total_steps,
                    'tools_used': result.tools_used,
                    'metadata': result.metadata,
                })
                
                # Aggregate metadata
                self._aggregated_results['total_steps'] += result.total_steps
                self._aggregated_results['total_tools_used'].update(result.tools_used)
                self._aggregated_results['total_execution_time'] += result.metadata.get('execution_time_seconds', 0.0)
                
                return result.text
            finally:
                # Remove from call stack
                self._call_stack.pop()
        
        # Create and return the tool
        return Tool(
            name=agent.config.name,
            description=description,
            func=agent_wrapper,
            metadata=metadata,
        )

    def get_plan(self) -> Optional[Plan]:
        """
        Get the current execution plan.

        Returns:
            Current plan or None if no plan exists
        """
        if self.state and self.state.plan:
            return self.state.plan
        return None

    def get_plan_display(self) -> str:
        """
        Get formatted plan for display.

        Returns:
            Formatted plan string or message if no plan exists
        """
        plan = self.get_plan()
        if plan:
            return format_plan_for_display(plan)
        return "No plan available"

    def get_aggregated_results(self) -> Dict[str, Any]:
        """
        Get aggregated results from multi-agent collaboration.

        Returns:
            Dictionary containing aggregated metadata from all agent calls,
            including total steps, tools used, execution time, and individual
            agent call details.
        """
        if not hasattr(self, '_aggregated_results'):
            return {
                'agent_calls': [],
                'total_steps': 0,
                'total_tools_used': [],
                'total_execution_time': 0.0,
            }
        
        # Convert set to list for JSON serialization
        results = self._aggregated_results.copy()
        results['total_tools_used'] = list(results['total_tools_used'])
        return results

    def _reset_aggregated_results(self) -> None:
        """Reset aggregated results for a new execution."""
        self._aggregated_results = {
            'agent_calls': [],
            'total_steps': 0,
            'total_tools_used': set(),
            'total_execution_time': 0.0,
        }

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.config.name}, "
            f"role={self.config.role}, "
            f"tools={len(self.tools)})"
        )
