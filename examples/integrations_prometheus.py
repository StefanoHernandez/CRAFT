"""
Prometheus Integration Example

Demonstrates metrics collection and monitoring with Prometheus.
"""

import os
import time
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations import PrometheusExporter

# Example 1: Basic metrics
def basic_metrics():
    """Basic chatbot with Prometheus metrics."""
    # Initialize exporter (starts HTTP server on port 8000)
    exporter = PrometheusExporter(
        port=8000,
        namespace="craft",
    )

    # Create chatbot
    provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    chatbot = Chatbot(provider=provider)

    # Wrap with metrics
    monitored_chatbot = exporter.wrap_chatbot(chatbot)

    # Metrics automatically collected
    response = monitored_chatbot.chat("What is machine learning?")
    print(response.content)

    print("\nMetrics available at: http://localhost:8000")
    print("Prometheus scrape endpoint: http://localhost:8000/metrics")


# Example 2: Custom labels
def custom_labels():
    """Add custom labels to metrics."""
    exporter = PrometheusExporter(
        port=8001,
        namespace="myapp",
        labels={
            "environment": "production",
            "service": "chatbot",
            "version": "1.0.0",
        },
    )

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    monitored_chatbot = exporter.wrap_chatbot(chatbot)

    # All metrics include custom labels
    monitored_chatbot.chat("Hello!")

    print("Custom labels added to all metrics")


# Example 3: Manual metric recording
def manual_metrics():
    """Manually record custom metrics."""
    exporter = PrometheusExporter(port=8002)

    # Record request
    exporter.record_request(
        provider="anthropic",
        model="claude-sonnet-4.5",
        status="success",
    )

    # Record response time
    exporter.record_response_time(
        provider="anthropic",
        operation="chat",
        duration=1.5,
    )

    # Record token usage
    exporter.record_tokens(
        provider="anthropic",
        token_type="input",
        count=100,
    )
    exporter.record_tokens(
        provider="anthropic",
        token_type="output",
        count=50,
    )

    # Record error
    exporter.record_error(
        provider="anthropic",
        error_type="RateLimitError",
    )

    print("Manual metrics recorded")


# Example 4: Monitoring multiple chatbots
def multiple_chatbots():
    """Monitor multiple chatbots with one exporter."""
    # Single exporter for all chatbots
    exporter = PrometheusExporter(port=8003)

    # Multiple providers
    anthropic = AnthropicProvider()
    chatbot1 = exporter.wrap_chatbot(Chatbot(provider=anthropic))

    openai = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
    chatbot2 = exporter.wrap_chatbot(Chatbot(provider=openai))

    # Each chatbot tracked separately by provider label
    chatbot1.chat("Hello from Anthropic!")
    chatbot2.chat("Hello from OpenAI!")

    print("Multiple chatbots monitored")
    print("Metrics differentiated by 'provider' label")


# Example 5: Production monitoring
def production_monitoring():
    """Production-ready monitoring setup."""
    exporter = PrometheusExporter(
        port=9090,  # Standard Prometheus port
        namespace="craft_prod",
        labels={
            "environment": "production",
            "datacenter": "us-east-1",
            "service": "customer_support",
        },
    )

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    monitored_chatbot = exporter.wrap_chatbot(chatbot)

    # Simulate production traffic
    queries = [
        "How do I reset my password?",
        "What are your business hours?",
        "I need help with my account",
    ]

    print("Simulating production traffic...")
    for query in queries:
        try:
            response = monitored_chatbot.chat(query)
            print(f"✓ Processed: {query[:30]}...")
        except Exception as e:
            print(f"✗ Error: {e}")
        time.sleep(1)

    print("\n📊 Metrics Dashboard:")
    print("- Total requests: craft_prod_chat_requests_total")
    print("- Response time: craft_prod_response_time_seconds")
    print("- Token usage: craft_prod_tokens_total")
    print("- Error rate: craft_prod_errors_total")
    print(f"\nScrape at: http://localhost:9090/metrics")


# Example 6: Grafana integration
def grafana_example():
    """Example Prometheus queries for Grafana."""
    print("Grafana Dashboard Queries:")
    print("\n1. Request Rate (per second):")
    print("   rate(craft_chat_requests_total[5m])")

    print("\n2. Average Response Time:")
    print("   rate(craft_response_time_seconds_sum[5m]) / rate(craft_response_time_seconds_count[5m])")

    print("\n3. Error Rate:")
    print("   rate(craft_errors_total[5m]) / rate(craft_chat_requests_total[5m])")

    print("\n4. Token Usage (tokens/second):")
    print("   rate(craft_tokens_total[5m])")

    print("\n5. P95 Response Time:")
    print("   histogram_quantile(0.95, rate(craft_response_time_seconds_bucket[5m]))")

    print("\n6. Requests by Provider:")
    print("   sum by (provider) (rate(craft_chat_requests_total[5m]))")


if __name__ == "__main__":
    print("Prometheus Integration Examples\n")

    # Run examples
    print("1. Basic metrics...")
    basic_metrics()
    time.sleep(2)

    print("\n2. Custom labels...")
    custom_labels()
    time.sleep(2)

    print("\n3. Manual metrics...")
    manual_metrics()
    time.sleep(2)

    print("\n4. Multiple chatbots...")
    try:
        from craft.providers import OpenAIProvider
        multiple_chatbots()
    except ImportError:
        print("Skipped - OpenAI provider not configured")
    time.sleep(2)

    print("\n5. Production monitoring...")
    production_monitoring()

    print("\n6. Grafana queries...")
    grafana_example()

    print("\n✅ All examples completed!")
    print("\n📝 Next steps:")
    print("1. Configure Prometheus to scrape http://localhost:8000/metrics")
    print("2. Import dashboard to Grafana")
    print("3. Set up alerts for error rates and latency")
