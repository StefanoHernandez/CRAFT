"""Integration components for web, API, and observability."""

# Production Observability Integrations (optional dependencies)
try:
    from craft.integrations.langfuse import LangfuseTracer
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

try:
    from craft.integrations.prometheus import PrometheusExporter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from craft.integrations.opentelemetry import OpenTelemetryTracer
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

try:
    from craft.integrations.sentry import SentryIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

__all__ = []

# Export available integrations
if LANGFUSE_AVAILABLE:
    __all__.append("LangfuseTracer")
if PROMETHEUS_AVAILABLE:
    __all__.append("PrometheusExporter")
if OPENTELEMETRY_AVAILABLE:
    __all__.append("OpenTelemetryTracer")
if SENTRY_AVAILABLE:
    __all__.append("SentryIntegration")
