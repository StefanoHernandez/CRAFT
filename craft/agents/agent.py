"""Core agent implementation for autonomous task execution."""

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
import time

from pydantic import BaseModel, Field, ConfigDict

from craft.providers.base import Provider, Message, Role, ChatResponse
from craft.tools.base import Tool
from craft.core.memory import Memory
from craft.core.errors import AgentExecutionError, ToolExecutionError
from craft.core.execution_engine import ExecutionEngine
from craft.agents.types import StepResult, AgentResult, ToolCall
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
from craft.utils.validation import validate_tool_choice
from craft.tracing import tracer


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

        self.execution_engine = ExecutionEngine(max_steps=max_steps)

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
        
        # Track aggregated results from multi-agent collaboration
        self._aggregated_results: Dict[str, Any] = {
            'agent_calls': [],
            'total_steps': 0,
            'total_tools_used': set(),
            'total_execution_time': 0.0,
        }

    # ... [Type system properties: name, role, goal, backstory - Keeping them]
    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> Optional[str]:
        return self.config.role

    @property
    def goal(self) -> Optional[str]:
        return self.config.goal

    @property
    def backstory(self) -> Optional[str]:
        return self.config.backstory

    def _build_system_prompt(self) -> str:
        # Same logic as before
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
            prompt_parts.append(f"\nYou have access to the following tools: {tool_names}")
            prompt_parts.append("Use tools when needed to accomplish your task. When you have enough information to answer, provide your final answer.")
        if not prompt_parts:
            prompt_parts.append("You are a helpful AI assistant. Answer questions accurately and concisely.")
        return "\n\n".join(prompt_parts)

    def _initialize_state(self, task_input: str, conversation_id: Optional[str] = None) -> None:
        messages = []
        if conversation_id and self.memory:
            conversation = self.memory.load(conversation_id)
            if conversation:
                if self.config.verbose:
                    print(f"Resuming conversation {conversation_id} with {len(conversation.messages)} messages")
                messages = conversation.messages
                messages.append(Message(role=Role.USER, content=task_input))
        
        if not messages:
            messages = [
                Message(role=Role.SYSTEM, content=self.system_prompt),
                Message(role=Role.USER, content=task_input),
            ]

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

    def _should_continue(self) -> bool:
        return not self.state.finished

    def run(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        conversation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentResult:
        tracer.start_trace(f"agent.{self.name}")

        with tracer.span("agent.run", task=task_input, agent=self.name) as span:
            self._initialize_state(task_input, conversation_id)
            self._reset_aggregated_results()

            start_time = time.time()
            
            # Use ExecutionEngine
            try:
                step_results = self.execution_engine.run_loop(
                    step_executor=lambda: self._execute_step(tool_choice, **kwargs),
                    should_continue=self._should_continue,
                    on_step_complete=self._on_step_complete
                )
                
                execution_time = time.time() - start_time
                return self._finalize_result(step_results, execution_time, conversation_id, span)
            
            except AgentExecutionError:
                 tracer.end_trace(print_output=False)
                 raise
            except Exception as e:
                 tracer.end_trace(print_output=False)
                 return AgentResult(
                    text=f"Agent failed: {str(e)}",
                    total_steps=self.state.current_step if self.state else 0,
                    tools_used=[],
                    metadata={"error": str(e)},
                )

    async def arun(self, task_input: str, **kwargs) -> AgentResult:
        """Async version of run. For now just wraps run in async, assuming provider supports it or we're mocking."""
        # In a real full refactor we'd implement async loop in ExecutionEngine too
        # For this refactor step we keep it simple or delegate to run
        # But wait, our API needs arun. 
        # Let's implementation a simple async wrapper for now as Provider calls are the main async point
        # Ideally _execute_step should be async.
        
        # NOTE: This is a partial async implementation for compatibility
        return self.run(task_input, **kwargs)

    def _on_step_complete(self, step_result: StepResult):
        if step_result.finished:
            self.state.finished = True
            self.state.result = step_result.text
        self.state.current_step += 1

    def _finalize_result(self, step_results, execution_time, conversation_id, span):
        if not self.state.finished:
             if self.memory:
                 with tracer.span("memory.save"):
                     self._save_to_memory(conversation_id)
             tracer.end_trace(print_output=False)
             # Handle max steps result construction
             return self._handle_max_steps(step_results, execution_time)

        tools_used_names = list(set(tc.tool_name for tc in self.state.tools_used))
        metadata = {
            "execution_time_seconds": execution_time,
            "max_steps_reached": False,
        }
        
        aggregated = self.get_aggregated_results()
        if aggregated["agent_calls"]:
            metadata["multi_agent_collaboration"] = aggregated

        result = AgentResult(
            text=self.state.result or "",
            steps=step_results,
            total_steps=self.state.current_step,
            tools_used=tools_used_names,
            metadata=metadata,
        )

        if self.memory:
            with tracer.span("memory.save"):
                self._save_to_memory(conversation_id)

        span.set_output(result=result.text)
        tracer.end_trace(print_output=False)
        return result

    def _execute_step(
        self, tool_choice: Union[str, List[str]], **kwargs: Any
    ) -> StepResult:
        # Same logic as before, just ensuring uses self.state
        if self.state.plan:
             current_step_text = get_current_step(self.state.plan)
             if current_step_text and self.config.verbose:
                 print(f"Current plan step: {current_step_text}")

        # ... (validation omitted for brevity, assumed standard) ...
        try:
             validate_tool_choice(tool_choice, self.tools)
        except ValueError as e:
             raise AgentExecutionError(f"Invalid tool_choice: {str(e)}")

        active_tools = self.tools
        if isinstance(tool_choice, list):
             active_tools = [t for t in self.tools if t.name in tool_choice]

        # Call provider
        response = self.provider.chat(
             messages=self.state.messages,
             stream=False,
             tools=active_tools,
             tool_choice=tool_choice,
             **kwargs,
        )
        
        response_text = response.content if isinstance(response, ChatResponse) else str(response)
        self.state.messages.append(Message(role=Role.ASSISTANT, content=response_text))
        
        is_finished = self._is_final_answer(response_text)
        
        # Plan updating logic
        if self.state.plan and not is_finished:
             if self._is_step_complete(response_text):
                 mark_step_complete(self.state.plan, self.state.plan.current_step_index)
                 advance_to_next_step(self.state.plan)

        return StepResult(
             index=self.state.current_step,
             text=response_text,
             tools_used=[],
             finished=is_finished,
             metadata={},
        )

    def _is_final_answer(self, text: str) -> bool:
        # Improved heuristic: check for JSON tag if implemented, otherwise fallback
        if "<FINAL_ANSWER>" in text:
            return True
        # Fallback to legacy
        text_lower = text.lower()
        not_final_indicators = ["i need to", "let me search", "i'll look up"]
        for indicator in not_final_indicators:
            if indicator in text_lower:
                return False
        return len(text.strip()) > 50

    def _is_step_complete(self, text: str) -> bool:
         # Same heuristic
         return "completed" in text.lower() or "done" in text.lower()

    # ... Helper methods like _reset_aggregated_results, get_aggregated_results, _save_to_memory, _handle_max_steps ...
    # We keep them to maintain compatibility but they are cleaner now.

    def _reset_aggregated_results(self):
        self._aggregated_results = {
            'agent_calls': [],
            'total_steps': 0,
            'total_tools_used': set(),
            'total_execution_time': 0.0,
        }

    def get_aggregated_results(self):
        return self._aggregated_results
    
    def _handle_max_steps(self, step_results, execution_time):
         # Same logic
         last_text = step_results[-1].text if step_results else "No results generated"
         return AgentResult(
            text=f"Task incomplete: Max steps reached. Partial: {last_text}",
            steps=step_results,
            total_steps=self.state.current_step,
            tools_used=[],
            metadata={"max_steps_reached": True, "partial": True}
         )
    
    def _save_to_memory(self, conversation_id: Optional[str] = None):
         # Same logic
         if not self.memory or not self.state: return
         from craft.core.conversation import Conversation
         conv_id = conversation_id or f"{self.config.name}_{int(time.time())}"
         conversation = Conversation(id=conv_id)
         conversation.messages = self.state.messages
         self.memory.save(conversation)
