"""Main tracer implementation with decorators."""

import os
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager

from craft.tracing.context import TraceContext, TraceSpan, SpanStatus
from craft.tracing.formatter import TraceFormatter


class CraftTracer:
    """
    Global tracer singleton.
    
    Controls tracing via CRAFT_TRACE_CLIENT_IO environment variable:
    - 0: Disabled (default)
    - 1: Basic (agent steps only)
    - 2: Detailed (+ tool calls)
    - 3: Verbose (+ memory, I/O)
    """
    
    def __init__(self):
        self._current_context: Optional[TraceContext] = None
        self._current_span: Optional[TraceSpan] = None
        self._trace_level = int(os.getenv("CRAFT_TRACE_CLIENT_IO", "0"))
        self.formatter = TraceFormatter()
        
        # Initialize OpenTelemetry bridge if configured
        self._otel_bridge = None
        if os.getenv("OTEL_EXPORTER_TYPE"):
            try:
                from craft.tracing.otel_bridge import get_otel_bridge
                self._otel_bridge = get_otel_bridge()
            except ImportError:
                pass  # OTel not installed, continue with CRAFT-only tracing
    
    @property
    def enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._trace_level > 0
    
    @property
    def trace_level(self) -> int:
        """Get current trace level."""
        return self._trace_level
    
    def start_trace(self, name: str, **metadata) -> TraceContext:
        """Start a new trace context."""
        if not self.enabled:
            return None
        
        self._current_context = TraceContext(name=name, metadata=metadata)
        return self._current_context
    
    def end_trace(self, print_output: bool = True) -> Optional[TraceContext]:
        """
        End current trace and optionally print it.
        
        Args:
            print_output: If True, print trace before returning
        
        Returns:
            The completed trace context
        """
        if self._current_context:
            self._current_context.end()
            
            # Print before resetting context
            if print_output and self.enabled:
                output = self.formatter.format_trace(self._current_context)
                print(output)
        
        context = self._current_context
        self._current_context = None
        self._current_span = None
        
        return context
    
    @contextmanager
    def span(
        self,
        operation: str,
        level: int = 1,
        **inputs
    ):
        """
        Context manager for creating a trace span.
        
        Args:
            operation: Operation name (e.g., "agent.step", "tool.call")
            level: Minimum trace level required to record this span
            **inputs: Span inputs to capture
        
        Usage:
            with tracer.span("tool.call", query="test"):
                # Do work
                pass
        """
        # Skip if tracing disabled or level too low
        if not self.enabled or self._trace_level < level:
            yield None
            return
        
        # Create CRAFT span
        if not self._current_context:
            self._current_context = TraceContext(name="auto")
        
        parent = self._current_span
        craft_span = self._current_context.start_span(
            operation=operation,
            parent=parent,
            **inputs
        )
        
        # Set as current
        old_span = self._current_span
        self._current_span = craft_span
        
        # Also create OTel span if bridge is available
        otel_span_context = None
        if self._otel_bridge and self._otel_bridge.enabled:
            otel_span_context = self._otel_bridge.start_span(operation, **inputs)
            otel_span = otel_span_context.__enter__()
        
        try:
            yield craft_span
            craft_span.end(status=SpanStatus.SUCCESS)
            if otel_span_context:
                otel_span_context.__exit__(None, None, None)
        except Exception as e:
            craft_span.end(status=SpanStatus.ERROR, error=str(e))
            if otel_span_context:
                # Set error status on OTel span
                if otel_span:
                    from opentelemetry.trace import StatusCode
                    otel_span.set_status(StatusCode.ERROR, str(e))
                otel_span_context.__exit__(type(e), e, e.__traceback__)
            raise
        finally:
            self._current_span = old_span
    
    def print_trace(self) -> None:
        """Print current trace to console."""
        if self._current_context:
            output = self.formatter.format_trace(self._current_context)
            print(output)
    
    def get_current_context(self) -> Optional[TraceContext]:
        """Get current trace context."""
        return self._current_context


# Global tracer instance
tracer = CraftTracer()


# Decorators for easy tracing

def trace_agent_step(func: Callable) -> Callable:
    """Decorator to trace agent steps (level 1)."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with tracer.span("agent.step", level=1):
            return await func(*args, **kwargs)
    return wrapper


def trace_tool_call(func: Callable) -> Callable:
    """Decorator to trace tool calls (level 2)."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to extract tool name
        tool_name = kwargs.get("tool_name", "unknown")
        if hasattr(args[0], "name"):
            tool_name = args[0].name
        
        with tracer.span(f"tool.{tool_name}", level=2):
            return await func(*args, **kwargs)
    return wrapper


def trace_memory_access(func: Callable) -> Callable:
    """Decorator to trace memory access (level 3)."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with tracer.span("memory.access", level=3):
            return await func(*args, **kwargs)
    return wrapper
