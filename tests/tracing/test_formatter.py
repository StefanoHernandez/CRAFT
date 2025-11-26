"""Basic unit tests for tracing components."""

import pytest
from craft.tracing import TraceContext, TraceFormatter, SpanStatus


def test_formatter_basic_output():
    """Test formatter generates output."""
    ctx = TraceContext(name="test")
    span = ctx.start_span("operation")
    span.end()
    ctx.end()
    
    formatter = TraceFormatter()
    output = formatter.format_trace(ctx)
    
    assert "TRACE: test" in output
    assert "operation" in output.lower()
    assert "Summary" in output


def test_formatter_without_colors():
    """Test formatter works without colors."""
    ctx = TraceContext(name="test")
    span = ctx.start_span("operation")
    span.end()
    ctx.end()
    
    formatter = TraceFormatter(use_colors=False)
    output = formatter.format_trace(ctx)
    
    # Should not contain ANSI codes
    assert "\033[" not in output


def test_formatter_without_icons():
    """Test formatter works without icons."""
    ctx = TraceContext(name="test")
    span = ctx.start_span("operation")
    span.end()
    ctx.end()
    
    formatter = TraceFormatter(use_icons=False)
    output = formatter.format_trace(ctx)
    
    assert output is not None
    assert "test" in output
