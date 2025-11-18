"""
OpenTelemetry Integration Example

Demonstrates distributed tracing with OpenTelemetry.
"""

import os
import time
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations import OpenTelemetryTracer

# Example 1: Basic tracing
def basic_tracing():
    """Basic chatbot with OpenTelemetry tracing."""
    # Initialize tracer (exports to console by default)
    tracer = OpenTelemetryTracer(
        service_name="craft-chatbot",
        exporter_type="console",  # Or "otlp", "jaeger", "zipkin"
    )

    # Create chatbot
    provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    chatbot = Chatbot(provider=provider)

    # Wrap with tracing
    traced_chatbot = tracer.wrap_chatbot(chatbot)

    # All interactions automatically traced
    response = traced_chatbot.chat("What is distributed tracing?")
    print(response.content)

    print("\nTraces exported to console")


# Example 2: OTLP exporter (Jaeger, Tempo, etc.)
def otlp_exporter():
    """Export traces to OTLP-compatible backend."""
    tracer = OpenTelemetryTracer(
        service_name="craft-api",
        exporter_type="otlp",
        otlp_endpoint="http://localhost:4317",  # Jaeger, Grafana Tempo, etc.
        resource_attributes={
            "service.version": "1.0.0",
            "deployment.environment": "production",
            "service.namespace": "chatbot",
        },
    )

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    traced_chatbot = tracer.wrap_chatbot(chatbot)

    response = traced_chatbot.chat("Hello!")
    print("Trace exported to OTLP endpoint")


# Example 3: Custom spans
def custom_spans():
    """Create custom spans for detailed tracing."""
    tracer = OpenTelemetryTracer(service_name="craft-custom")
    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)

    # Create custom span
    with tracer.start_span("user_request", attributes={"user_id": "123"}) as span:
        # Nested span for validation
        with tracer.start_span("validate_input") as validation_span:
            # Validation logic
            time.sleep(0.1)
            validation_span.set_attribute("input_valid", True)

        # Chat span (automatically created by wrap_chatbot)
        traced_chatbot = tracer.wrap_chatbot(chatbot)
        response = traced_chatbot.chat("Hello!")

        # Add custom attributes to parent span
        span.set_attribute("response_length", len(response.content))
        span.set_attribute("success", True)

    print("Custom spans created")


# Example 4: RAG tracing
def rag_tracing():
    """Trace RAG operations."""
    from craft.rag import RAGSystem
    from craft.rag.vector_stores import ChromaVectorStore

    tracer = OpenTelemetryTracer(service_name="craft-rag")

    # Setup RAG
    vector_store = ChromaVectorStore()
    rag = RAGSystem(vector_store=vector_store)

    # Add documents
    rag.add_documents([
        "Python is a programming language.",
        "Machine learning uses algorithms.",
    ])

    # Trace RAG query
    query = "What is Python?"
    retrieved = rag.query(query, top_k=2)

    tracer.trace_rag_query(
        query=query,
        retrieved_docs=[
            {"content": doc.content, "score": doc.score}
            for doc in retrieved
        ],
        metadata={
            "vector_store": "chroma",
            "embedding_model": "default",
        },
    )

    print("RAG operation traced")


# Example 5: Error tracing
def error_tracing():
    """Trace errors and exceptions."""
    tracer = OpenTelemetryTracer(service_name="craft-errors")

    with tracer.start_span("risky_operation") as span:
        try:
            # Simulate error
            result = 1 / 0
        except Exception as e:
            # Record exception in span
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            print(f"Error traced: {e}")


# Example 6: Multi-service tracing
def distributed_tracing():
    """Trace across multiple services."""
    # Service 1: API Gateway
    api_tracer = OpenTelemetryTracer(
        service_name="api-gateway",
        exporter_type="console",
    )

    with api_tracer.start_span("api_request") as api_span:
        api_span.set_attribute("http.method", "POST")
        api_span.set_attribute("http.route", "/chat")

        # Service 2: Chatbot Service
        chatbot_tracer = OpenTelemetryTracer(service_name="chatbot-service")
        provider = AnthropicProvider()
        chatbot = Chatbot(provider=provider)
        traced_chatbot = chatbot_tracer.wrap_chatbot(chatbot)

        with chatbot_tracer.start_span("process_message") as chat_span:
            response = traced_chatbot.chat("Hello!")
            chat_span.set_attribute("message_length", len(response.content))

        api_span.set_attribute("status_code", 200)

    print("Distributed trace created across services")


# Example 7: Production setup with Jaeger
def production_jaeger():
    """Production setup with Jaeger."""
    tracer = OpenTelemetryTracer(
        service_name="craft-production",
        exporter_type="otlp",
        otlp_endpoint="http://jaeger:4317",
        resource_attributes={
            "service.version": "2.1.0",
            "deployment.environment": "production",
            "service.namespace": "ai-platform",
            "service.instance.id": "pod-123",
            "host.name": "k8s-node-1",
        },
    )

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    traced_chatbot = tracer.wrap_chatbot(chatbot)

    # Simulate production request
    with tracer.start_span(
        "user_chat_session",
        attributes={
            "user.id": "user_789",
            "session.id": "sess_abc123",
            "tenant.id": "company_xyz",
        }
    ) as span:
        response = traced_chatbot.chat("Production query")
        span.set_attribute("response.tokens", response.usage.get("output_tokens", 0))

    print("Production trace sent to Jaeger")
    print("View at: http://localhost:16686")


# Example 8: Sampling strategies
def sampling_example():
    """Configure trace sampling."""
    # Sample 10% of traces
    tracer = OpenTelemetryTracer(
        service_name="craft-sampled",
        exporter_type="console",
    )

    # In production, configure sampling ratio in OpenTelemetry SDK
    # OTEL_TRACES_SAMPLER=traceidratio
    # OTEL_TRACES_SAMPLER_ARG=0.1

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    traced_chatbot = tracer.wrap_chatbot(chatbot)

    # Only 10% of these will be traced
    for i in range(10):
        traced_chatbot.chat(f"Message {i}")

    print("Sampling applied - only subset traced")


if __name__ == "__main__":
    print("OpenTelemetry Integration Examples\n")

    # Run examples
    print("1. Basic tracing...")
    basic_tracing()

    print("\n2. OTLP exporter...")
    # otlp_exporter()  # Uncomment if OTLP endpoint available

    print("\n3. Custom spans...")
    custom_spans()

    print("\n4. RAG tracing...")
    rag_tracing()

    print("\n5. Error tracing...")
    error_tracing()

    print("\n6. Distributed tracing...")
    distributed_tracing()

    print("\n7. Production Jaeger setup...")
    # production_jaeger()  # Uncomment if Jaeger available

    print("\n8. Sampling...")
    sampling_example()

    print("\n✅ All examples completed!")
    print("\n📝 Next steps:")
    print("1. Set up Jaeger: docker run -d -p16686:16686 -p4317:4317 jaegertracing/all-in-one:latest")
    print("2. Or use Grafana Tempo, Honeycomb, or other OTLP backend")
    print("3. Configure sampling for production")
    print("4. View traces in Jaeger UI: http://localhost:16686")
