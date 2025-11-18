"""
Sentry Integration

Error tracking and performance monitoring with Sentry.
"""

from typing import Optional, Dict, Any, List
import functools

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


__all__ = ["SentryIntegration", "SENTRY_AVAILABLE", "configure_sentry"]


class SentryIntegration:
    """
    Sentry integration for CRAFT.

    Provides error tracking, performance monitoring, and user context.

    Examples:
        # Initialize
        sentry = SentryIntegration(
            dsn="https://...@sentry.io/...",
            environment="production",
            traces_sample_rate=0.1,
        )

        # Wrap chatbot
        chatbot = Chatbot(provider=provider)
        monitored_chatbot = sentry.wrap_chatbot(chatbot)

        # Errors and performance automatically tracked
        response = monitored_chatbot.chat("Hello!")
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: str = "production",
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
        release: Optional[str] = None,
        enabled: bool = True,
        **sentry_options,
    ):
        """
        Initialize Sentry integration.

        Args:
            dsn: Sentry DSN (or set SENTRY_DSN env var)
            environment: Environment name
            traces_sample_rate: APM sampling rate (0.0-1.0)
            profiles_sample_rate: Profiling sampling rate (0.0-1.0)
            release: Release version
            enabled: Enable/disable Sentry
            **sentry_options: Additional Sentry options
        """
        if not SENTRY_AVAILABLE:
            raise ImportError(
                "Sentry SDK is not installed. Install with: pip install sentry-sdk"
            )

        self.enabled = enabled
        if not self.enabled:
            return

        # Get version
        if release is None:
            try:
                from craft import __version__
                release = f"craft@{__version__}"
            except:
                release = "craft@unknown"

        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            release=release,
            integrations=[
                LoggingIntegration(level=None, event_level="ERROR"),
            ],
            **sentry_options,
        )

    def set_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        **additional_data,
    ) -> None:
        """
        Set user context for error tracking.

        Args:
            user_id: User ID
            email: User email
            username: Username
            **additional_data: Additional user data
        """
        if not self.enabled:
            return

        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username,
            **additional_data,
        })

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag for all events."""
        if self.enabled:
            sentry_sdk.set_tag(key, value)

    def set_context(self, name: str, data: Dict[str, Any]) -> None:
        """Set context data for events."""
        if self.enabled:
            sentry_sdk.set_context(name, data)

    def capture_exception(
        self,
        error: Exception,
        level: str = "error",
        **extra,
    ) -> None:
        """
        Manually capture an exception.

        Args:
            error: Exception to capture
            level: Error level (error/warning/info)
            **extra: Additional context
        """
        if not self.enabled:
            return

        with sentry_sdk.push_scope() as scope:
            scope.level = level
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        **extra,
    ) -> None:
        """
        Capture a message.

        Args:
            message: Message text
            level: Message level
            **extra: Additional context
        """
        if not self.enabled:
            return

        with sentry_sdk.push_scope() as scope:
            scope.level = level
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message)

    def start_transaction(
        self,
        name: str,
        op: str = "task",
        **kwargs,
    ):
        """
        Start a performance transaction.

        Args:
            name: Transaction name
            op: Operation type
            **kwargs: Additional transaction data

        Returns:
            Transaction context manager
        """
        if not self.enabled:
            from contextlib import nullcontext
            return nullcontext()

        return sentry_sdk.start_transaction(name=name, op=op, **kwargs)

    def wrap_chatbot(self, chatbot):
        """
        Wrap a chatbot to automatically track errors and performance.

        Args:
            chatbot: CRAFT Chatbot instance

        Returns:
            Wrapped chatbot with Sentry monitoring
        """
        if not self.enabled:
            return chatbot

        original_chat = chatbot.chat

        def monitored_chat(message: str, **kwargs):
            # Start transaction for performance monitoring
            with self.start_transaction(
                name="chatbot.chat",
                op="ai.chat",
            ) as transaction:
                try:
                    # Set context
                    self.set_context("chat", {
                        "provider": chatbot.provider.name,
                        "conversation_id": chatbot.conversation.id,
                        "message_length": len(message),
                    })

                    # Create span for LLM call
                    with transaction.start_child(
                        op="ai.llm.call",
                        description=f"LLM call to {chatbot.provider.name}",
                    ) as span:
                        response = original_chat(message, **kwargs)

                        # Add response metadata
                        span.set_data("response_length", len(response.content))
                        if response.usage:
                            span.set_data("tokens_input", response.usage.get("input_tokens"))
                            span.set_data("tokens_output", response.usage.get("output_tokens"))

                    return response

                except Exception as e:
                    # Capture exception with context
                    self.capture_exception(
                        e,
                        message=message[:100],
                        provider=chatbot.provider.name,
                        conversation_id=chatbot.conversation.id,
                    )
                    raise

        chatbot.chat = monitored_chat
        return chatbot

    def trace_function(self, op: str = "function"):
        """
        Decorator to trace function execution.

        Args:
            op: Operation type

        Examples:
            @sentry.trace_function(op="custom.operation")
            def my_function():
                ...
        """
        def decorator(func):
            if not self.enabled:
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                transaction = sentry_sdk.get_current_scope().transaction
                if transaction:
                    with transaction.start_child(
                        op=op,
                        description=func.__name__,
                    ):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            return wrapper

        return decorator


def configure_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    **options,
) -> SentryIntegration:
    """
    Convenience function to configure Sentry.

    Args:
        dsn: Sentry DSN
        environment: Environment name
        **options: Additional Sentry options

    Returns:
        Configured SentryIntegration instance
    """
    return SentryIntegration(dsn=dsn, environment=environment, **options)
