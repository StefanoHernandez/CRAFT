"""
OpenTelemetry Integration

Distributed tracing and observability with OpenTelemetry.
"""

from typing import Optional, Dict, Any
import time

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
    OPENTELEMETRY_AVAILABLE = True  # Alias for consistency
except ImportError:
    OTEL_AVAILABLE = False
    OPENTELEMETRY_AVAILABLE = False


__all__ = ["OpenTelemetryTracer", "OPENTELEMETRY_AVAILABLE", "OTEL_AVAILABLE"]


class OpenTelemetryTracer:
    """
    OpenTelemetry integration for CRAFT.

    Provides distributed tracing across services.

    Examples:
        # Initialize
        tracer = OpenTelemetryTracer(
            service_name="craft-chatbot",
            endpoint="http://localhost:4317",
        )

        # Wrap chatbot
        chatbot = Chatbot(provider=provider)
        traced_chatbot = tracer.wrap_chatbot(chatbot)

        # Use normally - traces sent to collector
        response = traced_chatbot.chat("Hello!")
    """

    def __init__(
        self,
        service_name: str = "craft",
        endpoint: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize OpenTelemetry tracer.

        Args:
            service_name: Service name for tracing
            endpoint: OTLP collector endpoint (e.g., http://localhost:4317)
            headers: Optional headers for authentication
            enabled: Enable/disable tracing
        """
        if not OTEL_AVAILABLE:
            raise ImportError(
                "OpenTelemetry is not installed. Install with: "
                "pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
            )

        self.enabled = enabled
        if not self.enabled:
            return

        # Create resource
        resource = Resource(attributes={SERVICE_NAME: service_name})

        # Setup tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter if endpoint provided
        if endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers or {})
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(__name__)

    def trace_chat(
        self,
        message: str,
        provider_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a traced chat context.

        Args:
            message: User message
            provider_name: Provider name
            attributes: Additional attributes

        Returns:
            Context manager for tracing

        Examples:
            with tracer.trace_chat("Hello", "anthropic") as span:
                response = provider.chat([Message(...)])
                span.set_attribute("response.length", len(response.content))
        """
        if not self.enabled:
            from contextlib import nullcontext
            return nullcontext()

        span = self.tracer.start_span(
            "chat",
            attributes={
                "chat.message": message[:100],  # Truncate
                "chat.provider": provider_name,
                **(attributes or {}),
            },
        )

        return span

    def trace_rag_query(
        self,
        query: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a traced RAG query context.

        Args:
            query: Search query
            attributes: Additional attributes

        Returns:
            Context manager for tracing
        """
        if not self.enabled:
            from contextlib import nullcontext
            return nullcontext()

        return self.tracer.start_span(
            "rag.query",
            attributes={
                "rag.query": query[:100],
                **(attributes or {}),
            },
        )

    def wrap_chatbot(self, chatbot):
        """
        Wrap a chatbot to automatically trace all interactions.

        Args:
            chatbot: CRAFT Chatbot instance

        Returns:
            Wrapped chatbot with tracing
        """
        if not self.enabled:
            return chatbot

        original_chat = chatbot.chat

        def traced_chat(message: str, **kwargs):
            with self.tracer.start_as_current_span(
                "chatbot.chat",
                attributes={
                    "chat.message": message[:100],
                    "chat.provider": chatbot.provider.name,
                    "chat.conversation_id": chatbot.conversation.id,
                },
            ) as span:
                try:
                    start_time = time.time()
                    response = original_chat(message, **kwargs)

                    # Add response attributes
                    span.set_attribute("chat.response.length", len(response.content))
                    span.set_attribute(
                        "chat.response.time_ms", (time.time() - start_time) * 1000
                    )

                    if response.usage:
                        span.set_attribute(
                            "chat.tokens.input",
                            response.usage.get("input_tokens", 0),
                        )
                        span.set_attribute(
                            "chat.tokens.output",
                            response.usage.get("output_tokens", 0),
                        )

                    span.set_status(Status(StatusCode.OK))
                    return response

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        chatbot.chat = traced_chat
        return chatbot

    def wrap_rag_engine(self, rag_engine):
        """
        Wrap a RAG engine to trace retrievals.

        Args:
            rag_engine: CRAFT RetrievalEngine instance

        Returns:
            Wrapped engine with tracing
        """
        if not self.enabled:
            return rag_engine

        original_query = rag_engine.query

        def traced_query(query: str, **kwargs):
            with self.tracer.start_as_current_span(
                "rag.retrieval",
                attributes={
                    "rag.query": query[:100],
                },
            ) as span:
                try:
                    results = original_query(query, **kwargs)

                    span.set_attribute("rag.results.count", len(results))
                    if results:
                        span.set_attribute("rag.results.top_score", results[0].score)

                    span.set_status(Status(StatusCode.OK))
                    return results

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        rag_engine.query = traced_query
        return rag_engine
