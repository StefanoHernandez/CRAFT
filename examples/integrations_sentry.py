"""
Sentry Integration Example

Demonstrates error tracking and performance monitoring with Sentry.
"""

import os
import time
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations import SentryIntegration

# Example 1: Basic error tracking
def basic_error_tracking():
    """Basic chatbot with Sentry error tracking."""
    # Initialize Sentry
    sentry = SentryIntegration(
        dsn=os.getenv("SENTRY_DSN"),  # Or set SENTRY_DSN env var
        environment="production",
        traces_sample_rate=0.1,  # 10% of transactions
    )

    # Create chatbot
    provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    chatbot = Chatbot(provider=provider)

    # Wrap with Sentry
    monitored_chatbot = sentry.wrap_chatbot(chatbot)

    # Errors automatically captured
    try:
        response = monitored_chatbot.chat("What is error tracking?")
        print(response.content)
    except Exception as e:
        print(f"Error captured by Sentry: {e}")


# Example 2: User context
def user_context():
    """Track errors with user context."""
    sentry = SentryIntegration(
        dsn=os.getenv("SENTRY_DSN"),
        environment="production",
    )

    # Set user context
    sentry.set_user(
        user_id="user_123",
        email="user@example.com",
        username="john_doe",
        subscription="premium",
        organization="Acme Corp",
    )

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    monitored_chatbot = sentry.wrap_chatbot(chatbot)

    # Errors include user context
    response = monitored_chatbot.chat("Hello!")
    print("User context attached to all events")


# Example 3: Custom tags and context
def custom_context():
    """Add custom tags and context."""
    sentry = SentryIntegration()

    # Set tags (for filtering in Sentry)
    sentry.set_tag("feature", "customer_support")
    sentry.set_tag("version", "2.1.0")
    sentry.set_tag("deployment", "us-east-1")

    # Set context data
    sentry.set_context("business", {
        "customer_tier": "enterprise",
        "account_id": "acc_789",
        "plan": "unlimited",
    })

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    monitored_chatbot = sentry.wrap_chatbot(chatbot)

    response = monitored_chatbot.chat("Test message")
    print("Custom tags and context added")


# Example 4: Manual exception capture
def manual_exceptions():
    """Manually capture exceptions with context."""
    sentry = SentryIntegration()

    try:
        # Risky operation
        result = perform_complex_operation()
    except ValueError as e:
        # Capture with custom context
        sentry.capture_exception(
            e,
            level="error",
            user_input="invalid data",
            operation="data_processing",
            attempt_number=3,
        )
        print("Exception captured with context")

def perform_complex_operation():
    raise ValueError("Invalid configuration")


# Example 5: Performance monitoring
def performance_monitoring():
    """Monitor performance with transactions."""
    sentry = SentryIntegration(
        traces_sample_rate=1.0,  # 100% sampling for demo
        profiles_sample_rate=1.0,
    )

    # Start transaction
    with sentry.start_transaction(
        name="chat_flow",
        op="user.interaction",
    ) as transaction:
        # Span 1: Input validation
        with transaction.start_child(
            op="validation",
            description="Validate user input",
        ) as span:
            time.sleep(0.1)
            span.set_data("input_length", 50)

        # Span 2: LLM call (automatically tracked by wrap_chatbot)
        provider = AnthropicProvider()
        chatbot = Chatbot(provider=provider)
        monitored_chatbot = sentry.wrap_chatbot(chatbot)
        response = monitored_chatbot.chat("Test")

        # Span 3: Post-processing
        with transaction.start_child(
            op="postprocess",
            description="Format response",
        ) as span:
            time.sleep(0.05)
            span.set_data("output_length", len(response.content))

        transaction.set_data("total_tokens", response.usage.get("total_tokens", 0))

    print("Performance transaction recorded")


# Example 6: Function tracing decorator
def decorator_example():
    """Use decorator for function tracing."""
    sentry = SentryIntegration(traces_sample_rate=1.0)

    @sentry.trace_function(op="ai.processing")
    def process_message(message: str) -> str:
        """Automatically traced function."""
        time.sleep(0.2)
        return f"Processed: {message}"

    with sentry.start_transaction(name="user_request", op="request"):
        result = process_message("Hello World")
        print(result)

    print("Function traced with decorator")


# Example 7: Message capture
def message_capture():
    """Capture informational messages."""
    sentry = SentryIntegration()

    # Capture info message
    sentry.capture_message(
        "User started chat session",
        level="info",
        user_id="user_456",
        feature="chat",
    )

    # Capture warning
    sentry.capture_message(
        "Rate limit approaching",
        level="warning",
        current_usage=95,
        limit=100,
    )

    print("Messages captured")


# Example 8: Production setup
def production_setup():
    """Production-ready Sentry configuration."""
    sentry = SentryIntegration(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENVIRONMENT", "production"),
        release=os.getenv("RELEASE_VERSION", "1.0.0"),
        traces_sample_rate=0.1,  # 10% sampling
        profiles_sample_rate=0.1,

        # Additional Sentry options
        send_default_pii=False,  # Don't send PII
        attach_stacktrace=True,
        max_breadcrumbs=50,
        before_send=lambda event, hint: event,  # Filter events if needed
    )

    # Set release context
    sentry.set_tag("service", "chatbot-api")
    sentry.set_tag("datacenter", "us-east-1")

    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)
    monitored_chatbot = sentry.wrap_chatbot(chatbot)

    # Production traffic
    try:
        response = monitored_chatbot.chat("Production query")
        print("✓ Request successful")
    except Exception as e:
        print(f"✗ Error tracked: {e}")

    print("Production monitoring active")


# Example 9: Multiple environments
def multiple_environments():
    """Different configs for different environments."""
    environment = os.getenv("ENV", "development")

    if environment == "production":
        sentry = SentryIntegration(
            environment="production",
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
    elif environment == "staging":
        sentry = SentryIntegration(
            environment="staging",
            traces_sample_rate=0.5,  # Higher sampling
            profiles_sample_rate=0.5,
        )
    else:
        sentry = SentryIntegration(
            environment="development",
            traces_sample_rate=1.0,  # 100% sampling
            profiles_sample_rate=1.0,
        )

    print(f"Sentry configured for {environment}")


# Example 10: Error filtering
def error_filtering():
    """Filter which errors to send to Sentry."""
    def before_send(event, hint):
        """Filter events before sending."""
        # Don't send certain errors
        if "exception" in event:
            exc = hint.get("exc_info")
            if exc and isinstance(exc[1], KeyboardInterrupt):
                return None  # Don't send

        # Add custom data
        event["tags"]["filtered"] = "yes"
        return event

    sentry = SentryIntegration(
        before_send=before_send,
    )

    print("Error filtering configured")


if __name__ == "__main__":
    print("Sentry Integration Examples\n")

    # Check if SENTRY_DSN is set
    if not os.getenv("SENTRY_DSN"):
        print("⚠️  SENTRY_DSN not set. Some examples will be skipped.")
        print("Set it with: export SENTRY_DSN='https://...@sentry.io/...'")
        print()

    # Run examples
    print("1. Basic error tracking...")
    # basic_error_tracking()  # Uncomment if SENTRY_DSN is set

    print("\n2. User context...")
    user_context()

    print("\n3. Custom context...")
    custom_context()

    print("\n4. Manual exceptions...")
    manual_exceptions()

    print("\n5. Performance monitoring...")
    performance_monitoring()

    print("\n6. Decorator example...")
    decorator_example()

    print("\n7. Message capture...")
    message_capture()

    print("\n8. Production setup...")
    # production_setup()  # Uncomment if SENTRY_DSN is set

    print("\n9. Multiple environments...")
    multiple_environments()

    print("\n10. Error filtering...")
    error_filtering()

    print("\n✅ All examples completed!")
    print("\n📝 Next steps:")
    print("1. Sign up at sentry.io or deploy self-hosted Sentry")
    print("2. Get your DSN from project settings")
    print("3. Set SENTRY_DSN environment variable")
    print("4. Configure alerts and notifications in Sentry dashboard")
    print("5. Set up issue assignment and workflow automation")
