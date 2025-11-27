"""OpenTelemetry bridge for CRAFT tracing system.

This module integrates OpenTelemetry SDK with CRAFT's existing tracing,
enabling export to Jaeger, Zipkin, OTLP while maintaining backward compatibility.
"""

import os
from typing import Optional
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    
    # Optional exporters
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        JAEGER_AVAILABLE = True
    except ImportError:
        JAEGER_AVAILABLE = False
    
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        OTLP_AVAILABLE = True
    except ImportError:
        OTLP_AVAILABLE = False
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class OTelBridge:
    """
    Bridge between CRAFT's tracing and OpenTelemetry.
    
    Environment Variables:
        OTEL_EXPORTER_TYPE: console | jaeger | otlp (default: none)
        OTEL_SERVICE_NAME: Service name in traces (default: craft-agent)
        OTEL_EXPORTER_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
        JAEGER_AGENT_HOST: Jaeger host (default: localhost)
        JAEGER_AGENT_PORT: Jaeger port (default: 6831)
    """
    
    def __init__(self):
        self._tracer: Optional[trace.Tracer] = None
        self._provider: Optional[TracerProvider] = None
        
        if not OTEL_AVAILABLE:
            return
        
        exporter_type = os.getenv("OTEL_EXPORTER_TYPE", "").lower()
        if not exporter_type:
            return  # OTel disabled
        
        # Initialize TracerProvider
        service_name = os.getenv("OTEL_SERVICE_NAME", "craft-agent")
        resource = Resource(attributes={SERVICE_NAME: service_name})
        
        self._provider = TracerProvider(resource=resource)
        
        # Configure exporter
        exporter = self._create_exporter(exporter_type)
        if exporter:
            processor = BatchSpanProcessor(exporter)
            self._provider.add_span_processor(processor)
            
            # Set as global tracer provider
            trace.set_tracer_provider(self._provider)
            self._tracer = trace.get_tracer(__name__)
    
    def _create_exporter(self, exporter_type: str):
        """Create span exporter based on type."""
        if exporter_type == "console":
            return ConsoleSpanExporter()
        
        elif exporter_type == "jaeger":
            if not JAEGER_AVAILABLE:
                raise ImportError(
                    "Jaeger exporter not available. "
                    "Install with: pip install opentelemetry-exporter-jaeger"
                )
            agent_host = os.getenv("JAEGER_AGENT_HOST", "localhost")
            agent_port = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
            
            return JaegerExporter(
                agent_host_name=agent_host,
                agent_port=agent_port,
            )
        
        elif exporter_type == "otlp":
            if not OTLP_AVAILABLE:
                raise ImportError(
                    "OTLP exporter not available. "
                    "Install with: pip install opentelemetry-exporter-otlp"
                )
            endpoint = os.getenv("OTEL_EXPORTER_ENDPOINT", "http://localhost:4317")
            return OTLPSpanExporter(endpoint=endpoint)
        
        else:
            raise ValueError(
                f"Unknown OTEL_EXPORTER_TYPE: {exporter_type}. "
                f"Valid options: console, jaeger, otlp"
            )
    
    @property
    def enabled(self) -> bool:
        """Check if OTel is enabled."""
        return self._tracer is not None
    
    @contextmanager
    def start_span(self, operation: str, **attributes):
        """
        Create an OTel span.
        
        Args:
            operation: Span name
            **attributes: Span attributes
            
        Yields:
            OTel span or None if disabled
        """
        if not self._tracer:
            yield None
            return
        
        with self._tracer.start_as_current_span(operation) as span:
            # Add attributes
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, str(value))
            
            yield span
    
    def shutdown(self):
        """Shutdown tracer provider and flush pending spans."""
        if self._provider:
            self._provider.shutdown()


# Global OTel bridge instance
_otel_bridge: Optional[OTelBridge] = None


def get_otel_bridge() -> OTelBridge:
    """Get or create global OTel bridge."""
    global _otel_bridge
    if _otel_bridge is None:
        _otel_bridge = OTelBridge()
    return _otel_bridge


def shutdown_otel():
    """Shutdown OTel and flush spans."""
    global _otel_bridge
    if _otel_bridge:
        _otel_bridge.shutdown()
        _otel_bridge = None
