"""Property-based tests for tracing system using Hypothesis."""

import pytest
import os
from hypothesis import given, strategies as st, settings, HealthCheck

from craft.tracing import TraceContext, TraceSpan, SpanStatus, tracer


class TestTraceContext:
    """Tests for TraceContext."""
    
    def test_context_creation(self):
        """Test basic context creation."""
        ctx = TraceContext(name="test")
        assert ctx.name == "test"
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) == 8  # UUID prefix
    
    def test_start_span(self):
        """Test starting a span."""
        ctx = TraceContext(name="test")
        span = ctx.start_span("operation.test", key="value")
        
        assert span.operation == "operation.test"
        assert span.inputs == {"key": "value"}
        assert span in ctx.roots
    
    def test_nested_spans(self):
        """Test nested span creation."""
        ctx = TraceContext(name="test")
        
        parent = ctx.start_span("parent")
        child = ctx.start_span("child", parent=parent)
        
        assert child.parent_span_id == parent.span_id
        assert child in parent.children
    
    def test_get_all_spans(self):
        """Test getting all spans."""
        ctx = TraceContext(name="test")
        
        root = ctx.start_span("root")
        child1 = ctx.start_span("child1", parent=root)
        child2 = ctx.start_span("child2", parent=root)
        grandchild = ctx.start_span("grandchild", parent=child1)
        
        all_spans = ctx.get_all_spans()
        assert len(all_spans) == 4
        assert root in all_spans
        assert child1 in all_spans
        assert child2 in all_spans
        assert grandchild in all_spans
    
    def test_summary(self):
        """Test summary generation."""
        ctx = TraceContext(name="test")
        
        span1 = ctx.start_span("op1")
        span1.end(status=SpanStatus.SUCCESS)
        
        span2 = ctx.start_span("op2", parent=span1)
        span2.end(status=SpanStatus.ERROR)
        
        ctx.end()
        
        summary = ctx.get_summary()
        assert summary["total_spans"] == 2
        assert summary["successful_spans"] == 1
        assert summary["error_spans"] == 1


class TestTraceSpan:
    """Tests for TraceSpan."""
    
    def test_span_creation(self):
        """Test basic span creation."""
        span = TraceSpan(operation="test.op")
        assert span.operation == "test.op"
        assert span.status == SpanStatus.PENDING
        assert span.end_time is None
    
    def test_span_timing(self):
        """Test span timing."""
        span = TraceSpan(operation="test")
        assert span.duration >= 0
        
        span.end()
        assert span.end_time is not None
        assert span.status == SpanStatus.SUCCESS
        assert span.duration > 0
    
    def test_span_error(self):
        """Test span error handling."""
        span = TraceSpan(operation="test")
        span.end(status=SpanStatus.ERROR, error="Test error")
        
        assert span.status == SpanStatus.ERROR
        assert span.outputs["error"] == "Test error"


class TestCraftTracer:
    """Tests for CraftTracer."""
    
    def test_tracer_disabled_by_default(self):
        """Test tracer is disabled without env var."""
        # Reset env var
        if "CRAFT_TRACE_CLIENT_IO" in os.environ:
            del os.environ["CRAFT_TRACE_CLIENT_IO"]
        
        # Create new tracer instance
        from craft.tracing.tracer import CraftTracer
        test_tracer = CraftTracer()
        
        assert not test_tracer.enabled
        assert test_tracer.trace_level == 0
    
    def test_tracer_enabled_by_env(self):
        """Test tracer enabled by environment variable."""
        os.environ["CRAFT_TRACE_CLIENT_IO"] = "2"
        
        from craft.tracing.tracer import CraftTracer
        test_tracer = CraftTracer()
        
        assert test_tracer.enabled
        assert test_tracer.trace_level == 2
        
        # Cleanup
        del os.environ["CRAFT_TRACE_CLIENT_IO"]
    
    @pytest.mark.asyncio
    async def test_span_context_manager(self):
        """Test span context manager."""
        os.environ["CRAFT_TRACE_CLIENT_IO"] = "3"
        
        from craft.tracing.tracer import CraftTracer
        test_tracer = CraftTracer()
        
        test_tracer.start_trace("test")
        
        with test_tracer.span("operation.test", level=1, key="value") as span:
            assert span is not None
            assert span.operation == "operation.test"
            assert span.inputs == {"key": "value"}
        
        assert span.status == SpanStatus.SUCCESS
        
        test_tracer.end_trace(print_output=False)
        
        # Cleanup
        del os.environ["CRAFT_TRACE_CLIENT_IO"]


# Property-based tests

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
def test_trace_handles_arbitrary_operations(operations):
    """Test that tracing handles any sequence of operation names."""
    os.environ["CRAFT_TRACE_CLIENT_IO"] = "3"
    
    from craft.tracing.tracer import CraftTracer
    test_tracer = CraftTracer()
    
    test_tracer.start_trace("property_test")
    
    for op in operations:
        with test_tracer.span(op, level=1):
            pass
    
    ctx = test_tracer.end_trace(print_output=False)
    
    assert ctx is not None
    all_spans = ctx.get_all_spans()
    assert len(all_spans) == len(operations)
    
    # Cleanup
    del os.environ["CRAFT_TRACE_CLIENT_IO"]


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.integers(min_value=0, max_value=3))
def test_trace_level_validation(level):
    """Test that trace levels control verbosity correctly."""
    os.environ["CRAFT_TRACE_CLIENT_IO"] = str(level)
    
    from craft.tracing.tracer import CraftTracer
    test_tracer = CraftTracer()
    
    assert test_tracer.trace_level == level
    assert test_tracer.enabled == (level > 0)
    
    # Cleanup
    del os.environ["CRAFT_TRACE_CLIENT_IO"]


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    st.integers(min_value=1, max_value=5),
    st.integers(min_value=1, max_value=3)
)
def test_nested_spans_tree_structure(depth, breadth):
    """Test that nested spans maintain correct tree structure."""
    os.environ["CRAFT_TRACE_CLIENT_IO"] = "3"
    
    from craft.tracing.tracer import CraftTracer
    test_tracer = CraftTracer()
    
    ctx = TraceContext(name="property_test")
    
    def create_tree(parent, current_depth):
        if current_depth >= depth:
            return
        
        for i in range(breadth):
            span = ctx.start_span(f"op_d{current_depth}_b{i}", parent=parent)
            create_tree(span, current_depth + 1)
    
    root = ctx.start_span("root")
    create_tree(root, 1)
    
    all_spans = ctx.get_all_spans()
    
    # Calculate expected span count: 1 + breadth + breadth^2 + ... + breadth^depth
    expected = sum(breadth**i for i in range(depth))
    assert len(all_spans) == expected
    
    # Cleanup
    del os.environ["CRAFT_TRACE_CLIENT_IO"]
