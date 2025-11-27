"""Tracing and observability module."""

from craft.tracing.context import TraceContext, TraceSpan, SpanStatus
from craft.tracing.tracer import tracer, trace_agent_step, trace_tool_call, trace_memory_access
from craft.tracing.formatter import TraceFormatter

# OpenTelemetry integration (optional)
try:
    from craft.tracing.otel_bridge import get_otel_bridge, shutdown_otel
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    get_otel_bridge = None
    shutdown_otel = None

__all__ = [
    "TraceContext",
    "TraceSpan",
    "SpanStatus",
    "tracer",
    "trace_agent_step",
    "trace_tool_call",
    "trace_memory_access",
    "TraceFormatter",
    "get_otel_bridge",
    "shutdown_otel",
    "OTEL_AVAILABLE",
]
