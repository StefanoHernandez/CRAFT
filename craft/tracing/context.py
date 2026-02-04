"""Context tracking and trace tree generation."""

import time
import uuid
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict


class SpanStatus(str, Enum):
    """Status of a trace span."""
    
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class TraceSpan:
    """
    Individual trace span representing a single operation.
    
    Examples: agent.run, tool.call, memory.search, etc.
    """
    
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    operation: str = ""  # "agent.run", "tool.call", etc.
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.PENDING
    
    # Data
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Hierarchy
    parent_span_id: Optional[str] = None
    children: List["TraceSpan"] = field(default_factory=list)
    
    def end(self, status: SpanStatus = SpanStatus.SUCCESS, **outputs) -> None:
        """Mark span as complete."""
        self.end_time = time.time()
        self.status = status
        self.outputs.update(outputs)

    def set_output(self, **outputs) -> None:
        """Set output values without ending the span."""
        self.outputs.update(outputs)
    
    @property
    def duration(self) -> float:
        """Get span duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def add_child(self, span: "TraceSpan") -> None:
        """Add a child span."""
        span.parent_span_id = self.span_id
        self.children.append(span)


class TraceContext(BaseModel):
    """
    Manages execution context and trace tree.
    
    A trace context represents a complete execution trace
    with all its nested operations.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "trace"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Root spans (forest)
    roots: List[TraceSpan] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def start_span(
        self,
        operation: str,
        parent: Optional[TraceSpan] = None,
        **inputs
    ) -> TraceSpan:
        """Start a new span."""
        span = TraceSpan(
            operation=operation,
            inputs=inputs,
            parent_span_id=parent.span_id if parent else None
        )
        
        if parent:
            parent.add_child(span)
        else:
            self.roots.append(span)
        
        return span
    
    def end(self) -> None:
        """End the trace context."""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """Total trace duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_all_spans(self) -> List[TraceSpan]:
        """Get all spans in the trace (flattened)."""
        spans = []
        
        def collect(span: TraceSpan):
            spans.append(span)
            for child in span.children:
                collect(child)
        
        for root in self.roots:
            collect(root)
            
        return spans

    @property
    def spans(self) -> List[TraceSpan]:
        """Backward-compatible alias for all spans."""
        return self.get_all_spans()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get trace summary statistics."""
        all_spans = self.get_all_spans()
        
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "duration": self.duration,
            "total_spans": len(all_spans),
            "successful_spans": sum(1 for s in all_spans if s.status == SpanStatus.SUCCESS),
            "error_spans": sum(1 for s in all_spans if s.status == SpanStatus.ERROR),
            "pending_spans": sum(1 for s in all_spans if s.status == SpanStatus.PENDING),
        }
