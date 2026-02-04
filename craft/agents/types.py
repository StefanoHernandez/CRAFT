from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AgentError(BaseModel):
    """Structured error information for agent failures."""

    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
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
