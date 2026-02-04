"""Event system for agent streaming.

Defines event types and structures for real-time agent execution streaming
over WebSocket connections.
"""

from typing import Any, Dict, Optional, List, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class EventType(str, Enum):
    """Agent execution event types."""
    
    # Agent lifecycle
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"
    
    # Step events
    STEP_START = "step_start"
    STEP_END = "step_end"
    
    # Thought process
    THOUGHT = "thought"
    
    # Tool execution
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    TOOL_RESULT = "tool_result"
    
    # Response streaming
    RESPONSE_CHUNK = "response_chunk"
    RESPONSE_COMPLETE = "response_complete"
    
    # Planning
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    
    # Custom events
    CUSTOM = "custom"


class AgentEvent(BaseModel):
    """Base event from agent execution."""
    
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_name: str
    step_index: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat()
        }, use_enum_values=True)


class AgentStartEvent(AgentEvent):
    """Event when agent starts execution."""
    
    event_type: Literal[EventType.AGENT_START] = EventType.AGENT_START
    task: str
    max_steps: int


class AgentEndEvent(AgentEvent):
    """Event when agent completes execution."""
    
    event_type: Literal[EventType.AGENT_END] = EventType.AGENT_END
    result: str
    total_steps: int
    execution_time: float


class ThoughtEvent(AgentEvent):
    """Event for agent reasoning/thinking."""
    
    event_type: Literal[EventType.THOUGHT] = EventType.THOUGHT
    thought: str


class ToolCallStartEvent(AgentEvent):
    """Event when tool call begins."""
    
    event_type: Literal[EventType.TOOL_CALL_START] = EventType.TOOL_CALL_START
    tool_name: str
    arguments: Dict[str, Any]


class ToolCallEndEvent(AgentEvent):
    """Event when tool call completes."""
    
    event_type: Literal[EventType.TOOL_CALL_END] = EventType.TOOL_CALL_END
    tool_name: str
    result: Any
    success: bool
    error: Optional[str] = None


class ResponseChunkEvent(AgentEvent):
    """Event for streaming response chunks."""
    
    event_type: Literal[EventType.RESPONSE_CHUNK] = EventType.RESPONSE_CHUNK
    chunk: str
    is_final: bool = False


class PlanCreatedEvent(AgentEvent):
    """Event when plan is created."""
    
    event_type: Literal[EventType.PLAN_CREATED] = EventType.PLAN_CREATED
    plan_steps: List[str]
    total_steps: int


class EventEmitter:
    """
    Event emitter for agent execution events.
    
    Allows agents to emit events during execution that can be
    consumed by WebSocket connections or other listeners.
    
    Example:
        emitter = EventEmitter()
        
        # Listen to events
        async for event in emitter.events():
            print(f"Event: {event.event_type}")
        
        # Emit events
        await emitter.emit(ThoughtEvent(
            agent_name="my_agent",
            thought="I need to search for information"
        ))
    """
    
    def __init__(self):
        self._listeners: List[Any] = []  # asyncio.Queue objects
        self._history: List[AgentEvent] = []
        self._max_history = 100
    
    def add_listener(self, queue) -> None:
        """Add event listener queue."""
        self._listeners.append(queue)
    
    def remove_listener(self, queue) -> None:
        """Remove event listener queue."""
        if queue in self._listeners:
            self._listeners.remove(queue)
    
    async def emit(self, event: AgentEvent) -> None:
        """
        Emit event to all listeners.
        
        Args:
            event: Event to emit
        """
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Send to all listeners
        for listener in self._listeners:
            await listener.put(event)
    
    def get_history(self) -> List[AgentEvent]:
        """Get event history."""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()


# Global event emitter (can be replaced with per-agent emitters)
_global_emitter = EventEmitter()


def get_global_emitter() -> EventEmitter:
    """Get global event emitter."""
    return _global_emitter


# Helper functions for common events
async def emit_agent_start(agent_name: str, task: str, max_steps: int) -> None:
    """Emit agent start event."""
    await _global_emitter.emit(AgentStartEvent(
        agent_name=agent_name,
        task=task,
        max_steps=max_steps
    ))


async def emit_agent_end(agent_name: str, result: str, total_steps: int, execution_time: float) -> None:
    """Emit agent end event."""
    await _global_emitter.emit(AgentEndEvent(
        agent_name=agent_name,
        result=result,
        total_steps=total_steps,
        execution_time=execution_time
    ))


async def emit_thought(agent_name: str, thought: str, step_index: Optional[int] = None) -> None:
    """Emit thought event."""
    await _global_emitter.emit(ThoughtEvent(
        agent_name=agent_name,
        thought=thought,
        step_index=step_index
    ))


async def emit_tool_call_start(agent_name: str, tool_name: str, arguments: Dict, step_index: Optional[int] = None) -> None:
    """Emit tool call start event."""
    await _global_emitter.emit(ToolCallStartEvent(
        agent_name=agent_name,
        tool_name=tool_name,
        arguments=arguments,
        step_index=step_index
    ))


async def emit_tool_call_end(
    agent_name: str,
    tool_name: str,
    result: Any,
    success: bool,
    error: Optional[str] = None,
    step_index: Optional[int] = None
) -> None:
    """Emit tool call end event."""
    await _global_emitter.emit(ToolCallEndEvent(
        agent_name=agent_name,
        tool_name=tool_name,
        result=result,
        success=success,
        error=error,
        step_index=step_index
    ))


async def emit_response_chunk(agent_name: str, chunk: str, is_final: bool = False, step_index: Optional[int] = None) -> None:
    """Emit response chunk event."""
    await _global_emitter.emit(ResponseChunkEvent(
        agent_name=agent_name,
        chunk=chunk,
        is_final=is_final,
        step_index=step_index
    ))


async def emit_plan_created(agent_name: str, plan_steps: List[str]) -> None:
    """Emit plan created event."""
    await _global_emitter.emit(PlanCreatedEvent(
        agent_name=agent_name,
        plan_steps=plan_steps,
        total_steps=len(plan_steps)
    ))


if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demo event emission."""
        emitter = EventEmitter()
        
        # Emit some events
        await emitter.emit(AgentStartEvent(
            agent_name="demo_agent",
            task="Demonstrate event system",
            max_steps=5
        ))
        
        await emitter.emit(ThoughtEvent(
            agent_name="demo_agent",
            thought="I should start by understanding the task",
            step_index=0
        ))
        
        await emitter.emit(ToolCallStartEvent(
            agent_name="demo_agent",
            tool_name="search",
            arguments={"query": "event systems"},
            step_index=1
        ))
        
        # Print history
        print("Event History:")
        for event in emitter.get_history():
            print(f"  {event.event_type}: {event.data if hasattr(event, 'data') else event}")
    
    asyncio.run(demo())
