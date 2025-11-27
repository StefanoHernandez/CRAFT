"""Property tests for OpenTelemetry integration."""

import os
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch

from craft.tracing import tracer
from craft.tracing.context import TraceContext, SpanStatus


class TestOTelIntegration:
    """Property tests for OpenTelemetry integration."""
    
    def setup_method(self):
        """Reset tracer state before each test."""
        tracer._current_context = None
        tracer._current_span = None
        tracer._otel_bridge = None
    
    @given(
        operation=st.text(min_size=1, max_size=50),
        num_attrs=st.integers(min_value=0, max_value=10)
    )
    def test_property_span_attributes_preserved(self, operation, num_attrs):
        """
        Property: Attributes set on CRAFT spans should appear in OTel spans.
        
        This ensures that metadata captured by CRAFT is correctly
        propagated to OpenTelemetry for external observability tools.
        """
        # Mock OTel bridge
        mock_otel_bridge = Mock()
        mock_otel_bridge.enabled = True
        mock_otel_context = Mock()
        mock_otel_span = Mock()
        mock_otel_bridge.start_span.return_value = mock_otel_context
        mock_otel_context.__enter__.return_value = mock_otel_span
        mock_otel_context.__exit__.return_value = None
        
        tracer._otel_bridge = mock_otel_bridge
        tracer._trace_level = 1
        
        # Generate attributes
        attributes = {f"attr_{i}": f"value_{i}" for i in range(num_attrs)}
        
        # Create span with attributes
        with tracer.span(operation, **attributes):
            pass
        
        # Verify OTel bridge was called with same attributes
        if num_attrs > 0:
            mock_otel_bridge.start_span.assert_called_once()
            call_args = mock_otel_bridge.start_span.call_args
            assert call_args[0][0] == operation
            for key, value in attributes.items():
                assert call_args[1][key] == value
    
    @given(depth=st.integers(min_value=1, max_value=5))
    def test_property_nested_spans_hierarchy(self, depth):
        """
        Property: Nested span hierarchy should be preserved in OTel.
        
        When CRAFT spans are nested, the parent-child relationships
        must be correctly reflected in OpenTelemetry traces.
        """
        tracer._trace_level = 3
        
        # Track OTel span creation
        otel_spans_created = []
        
        def mock_start_span(operation, **attrs):
            context = Mock()
            span = Mock()
            otel_spans_created.append(operation)
            context.__enter__ = Mock(return_value=span)
            context.__exit__ = Mock(return_value=None)
            return context
        
        mock_otel_bridge = Mock()
        mock_otel_bridge.enabled = True
        mock_otel_bridge.start_span = mock_start_span
        
        tracer._otel_bridge = mock_otel_bridge
        
        # Create nested spans
        def create_nested(current_depth):
            if current_depth == 0:
                return
            with tracer.span(f"level_{current_depth}"):
                create_nested(current_depth - 1)
        
        create_nested(depth)
        
        # Verify all spans were created
        assert len(otel_spans_created) == depth
        for i in range(depth):
            assert f"level_{depth - i}" in otel_spans_created
    
    def test_context_propagation_async(self):
        """
        Test: Context propagation across async boundaries.
        
        OpenTelemetry context should be automatically propagated
        in async/await code without manual intervention.
        """
        import asyncio
        
        tracer._trace_level = 2
        
        async def inner_async_task():
            with tracer.span("inner_task"):
                await asyncio.sleep(0.01)  # Simulate async work
                return "done"
        
        async def outer_async_task():
            with tracer.span("outer_task"):
                result = await inner_async_task()
                return result
        
        # Run async code
        result = asyncio.run(outer_async_task())
        
        # Verify spans were created in context
        assert result == "done"
        assert tracer._current_context is not None
        assert len(tracer._current_context.spans) == 2
    
    @given(
        error_message=st.text(min_size=1, max_size=100)
    )
    def test_property_error_status_propagated(self, error_message):
        """
        Property: Errors should be captured in both CRAFT and OTel spans.
        """
        tracer._trace_level = 1
        
        mock_otel_span = Mock()
        mock_otel_context = Mock()
        mock_otel_context.__enter__ = Mock(return_value=mock_otel_span)
        mock_otel_context.__exit__ = Mock(return_value=None)
        
        mock_otel_bridge = Mock()
        mock_otel_bridge.enabled = True
        mock_otel_bridge.start_span = Mock(return_value=mock_otel_context)
        
        tracer._otel_bridge = mock_otel_bridge
        
        # Create span that raises error
        try:
            with tracer.span("error_test"):
                raise ValueError(error_message)
        except ValueError:
            pass  # Expected
        
        # Verify OTel span received error status
        mock_otel_span.set_status.assert_called_once()
        call_args = mock_otel_span.set_status.call_args[0]
        assert error_message in str(call_args[1])
    
    def test_otel_disabled_no_overhead(self):
        """
        Test: When OTel is disabled, there should be no overhead.
        """
        # Ensure OTel is disabled
        tracer._otel_bridge = None
        tracer._trace_level = 2
        
        # Create spans - should work without OTel
        with tracer.span("test_op"):
            pass
        
        # Verify CRAFT span was created
        assert tracer._current_context is not None
    
    def test_otel_graceful_fallback_on_import_error(self):
        """
        Test: If OpenTelemetry is not installed, CRAFT tracing continues.
        """
        # Simulate OTel not available
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "jaeger"}):
            with patch("craft.tracing.tracer.get_otel_bridge", side_effect=ImportError):
                # Re-initialize tracer
                from craft.tracing.tracer import CraftTracer
                test_tracer = CraftTracer()
                
                # Should continue without OTel
                assert test_tracer._otel_bridge is None
                test_tracer._trace_level = 1
                
                # Tracing should still work
                with test_tracer.span("test"):
                    pass
                
                assert test_tracer._current_context is not None


@pytest.mark.integration
class TestOTelExporters:
    """Integration tests for OTel exporters."""
    
    def test_console_exporter_initialization(self):
        """Test that console exporter can be initialized."""
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "console"}):
            from craft.tracing.otel_bridge import OTelBridge
            bridge = OTelBridge()
            assert bridge.enabled
    
    def test_invalid_exporter_type_raises(self):
        """Test that invalid exporter type raises clear error."""
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "invalid"}):
            from craft.tracing.otel_bridge import OTelBridge
            
            with pytest.raises(ValueError, match="Unknown OTEL_EXPORTER_TYPE"):
                OTelBridge()
