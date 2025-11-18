"""
Prometheus Metrics Exporter

Export CRAFT metrics to Prometheus for monitoring and alerting.
"""

from typing import Optional, Dict
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


__all__ = ["PrometheusExporter", "PROMETHEUS_AVAILABLE"]


class PrometheusExporter:
    """
    Prometheus metrics exporter for CRAFT.

    Exports metrics for monitoring chat operations, performance, and usage.

    Examples:
        # Initialize
        exporter = PrometheusExporter(namespace="craft")

        # Track metrics
        exporter.track_chat_request(provider="anthropic")
        exporter.track_response_time(0.5, provider="anthropic")
        exporter.track_tokens(150, token_type="input")

        # Expose metrics endpoint (FastAPI)
        @app.get("/metrics")
        def metrics():
            return Response(
                content=exporter.generate_metrics(),
                media_type="text/plain"
            )
    """

    def __init__(
        self,
        namespace: str = "craft",
        registry: Optional[object] = None,
    ):
        """
        Initialize Prometheus exporter.

        Args:
            namespace: Metrics namespace prefix
            registry: Custom registry (creates new if None)
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "prometheus_client is not installed. Install with: pip install prometheus-client"
            )

        self.namespace = namespace
        self.registry = registry or CollectorRegistry()

        # Define metrics
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics."""
        # Request counters
        self.chat_requests_total = Counter(
            f"{self.namespace}_chat_requests_total",
            "Total number of chat requests",
            ["provider", "status"],
            registry=self.registry,
        )

        self.rag_queries_total = Counter(
            f"{self.namespace}_rag_queries_total",
            "Total number of RAG queries",
            ["status"],
            registry=self.registry,
        )

        # Response time histograms
        self.response_time_seconds = Histogram(
            f"{self.namespace}_response_time_seconds",
            "Response time in seconds",
            ["provider", "operation"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry,
        )

        # Token usage
        self.tokens_total = Counter(
            f"{self.namespace}_tokens_total",
            "Total tokens used",
            ["provider", "type"],
            registry=self.registry,
        )

        # Active conversations
        self.active_conversations = Gauge(
            f"{self.namespace}_active_conversations",
            "Number of active conversations",
            registry=self.registry,
        )

        # Error counter
        self.errors_total = Counter(
            f"{self.namespace}_errors_total",
            "Total number of errors",
            ["type", "provider"],
            registry=self.registry,
        )

        # Info
        self.info = Info(
            f"{self.namespace}_info",
            "CRAFT service information",
            registry=self.registry,
        )

        # Set initial info
        from craft import __version__
        self.info.info({"version": __version__})

    def track_chat_request(
        self,
        provider: str,
        status: str = "success",
    ) -> None:
        """
        Track a chat request.

        Args:
            provider: Provider name
            status: Request status (success/error)
        """
        self.chat_requests_total.labels(provider=provider, status=status).inc()

    def track_response_time(
        self,
        duration: float,
        provider: str,
        operation: str = "chat",
    ) -> None:
        """
        Track response time.

        Args:
            duration: Duration in seconds
            provider: Provider name
            operation: Operation type
        """
        self.response_time_seconds.labels(provider=provider, operation=operation).observe(
            duration
        )

    def track_tokens(
        self,
        count: int,
        provider: str,
        token_type: str = "total",
    ) -> None:
        """
        Track token usage.

        Args:
            count: Number of tokens
            provider: Provider name
            token_type: Type of tokens (input/output/total)
        """
        self.tokens_total.labels(provider=provider, type=token_type).inc(count)

    def track_rag_query(self, status: str = "success") -> None:
        """Track RAG query."""
        self.rag_queries_total.labels(status=status).inc()

    def track_error(self, error_type: str, provider: str = "unknown") -> None:
        """
        Track an error.

        Args:
            error_type: Type of error
            provider: Provider name
        """
        self.errors_total.labels(type=error_type, provider=provider).inc()

    def set_active_conversations(self, count: int) -> None:
        """Set number of active conversations."""
        self.active_conversations.set(count)

    def generate_metrics(self) -> bytes:
        """
        Generate metrics in Prometheus format.

        Returns:
            Metrics as bytes
        """
        return generate_latest(self.registry)

    def wrap_chatbot(self, chatbot):
        """
        Wrap a chatbot to automatically track metrics.

        Args:
            chatbot: CRAFT Chatbot instance

        Returns:
            Wrapped chatbot with metrics tracking
        """
        original_chat = chatbot.chat

        def tracked_chat(message: str, **kwargs):
            provider = chatbot.provider.name
            start_time = time.time()

            try:
                response = original_chat(message, **kwargs)

                # Track success
                duration = time.time() - start_time
                self.track_chat_request(provider, "success")
                self.track_response_time(duration, provider)

                # Track tokens if available
                if response.usage:
                    if "input_tokens" in response.usage:
                        self.track_tokens(
                            response.usage["input_tokens"], provider, "input"
                        )
                    if "output_tokens" in response.usage:
                        self.track_tokens(
                            response.usage["output_tokens"], provider, "output"
                        )

                return response

            except Exception as e:
                # Track error
                self.track_chat_request(provider, "error")
                self.track_error(type(e).__name__, provider)
                raise

        chatbot.chat = tracked_chat
        return chatbot


class PrometheusMiddleware:
    """
    Prometheus middleware for FastAPI.

    Automatically tracks HTTP requests.
    """

    def __init__(self, app, exporter: PrometheusExporter):
        """
        Initialize middleware.

        Args:
            app: FastAPI app
            exporter: Prometheus exporter instance
        """
        self.app = app
        self.exporter = exporter

        # Add metrics endpoint
        from fastapi import Response

        @app.get("/metrics")
        async def metrics():
            return Response(
                content=self.exporter.generate_metrics(),
                media_type="text/plain",
            )
