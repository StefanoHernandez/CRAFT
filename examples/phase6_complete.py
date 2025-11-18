"""
Complete Phase 6 Example

Demonstrates all Phase 6 features working together:
- Multi-language support (i18n)
- Analytics & metrics tracking
- Monitoring & health checks
- Alerting system
"""

from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.storage import SQLiteStorage
from craft.core.memory import Memory
from craft.i18n import Translator, Language, detect_language
from craft.analytics import AnalyticsTracker, EventType, MetricType, MetricsCollector, Timer
from craft.monitoring import (
    HealthCheck,
    HealthStatus,
    ComponentHealth,
    AdvancedLogger,
    LogLevel,
    AlertManager,
    AlertLevel,
    console_alert_handler,
)
import os
import asyncio
import time


class ProductionChatbot:
    """
    Production-ready chatbot with full observability.

    Integrates:
    - Multi-language support
    - Analytics tracking
    - Health monitoring
    - Alerting
    """

    def __init__(self, api_key: str):
        """Initialize production chatbot."""
        # Setup logging
        self.logger = AdvancedLogger("production-chatbot", level=LogLevel.INFO)
        self.logger.info("Initializing production chatbot")

        # Setup storage
        self.storage = SQLiteStorage(database_path="./production.db")
        memory = Memory(storage=self.storage, max_messages=100)

        # Setup provider
        provider = AnthropicProvider(api_key=api_key)

        # Create chatbot
        self.chatbot = Chatbot(
            provider=provider,
            memory=memory,
            system_prompt="You are a helpful, multilingual AI assistant."
        )

        # Setup analytics
        self.analytics = AnalyticsTracker()
        self.metrics = MetricsCollector()

        # Setup health checks
        self.health = HealthCheck()
        self._setup_health_checks()

        # Setup alerts
        self.alerts = AlertManager()
        self.alerts.add_handler(AlertLevel.ERROR, console_alert_handler)

        # Current language
        self.translator = Translator(language=Language.ENGLISH)

        self.logger.info("Production chatbot initialized")

    def _setup_health_checks(self):
        """Setup health check components."""

        async def check_provider():
            return ComponentHealth(
                name="provider",
                status=HealthStatus.HEALTHY,
                message="Provider operational"
            )

        async def check_storage():
            try:
                count = self.storage.count()
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.HEALTHY,
                    message=f"Storage operational ({count} conversations)"
                )
            except Exception as e:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Storage error: {str(e)}"
                )

        self.health.add_check("provider", check_provider)
        self.health.add_check("storage", check_storage)

    async def chat(self, message: str, user_id: str = None) -> str:
        """
        Chat with full observability.

        Args:
            message: User message
            user_id: Optional user ID

        Returns:
            Assistant response
        """
        conversation_id = self.chatbot.conversation.id

        # Detect language
        detected_lang = detect_language(message)
        self.translator = Translator(language=detected_lang)

        # Log message
        self.logger.with_context(
            conversation_id=conversation_id,
            user_id=user_id,
            language=detected_lang.value
        ).info("Message received", message_length=len(message))

        # Track event
        self.analytics.track_event(
            EventType.MESSAGE_SENT,
            data={"message": message[:100], "length": len(message), "language": detected_lang.value},
            conversation_id=conversation_id,
            user_id=user_id
        )

        # Process with timing
        start_time = time.time()

        try:
            with Timer(self.metrics, MetricType.RESPONSE_TIME, tags={"language": detected_lang.value}):
                # Add language instruction
                lang_instruction = self.translator.translate_prompt("")
                if lang_instruction:
                    message = f"{lang_instruction}\n\n{message}"

                response = self.chatbot.chat(message)

            # Calculate metrics
            response_time = (time.time() - start_time) * 1000

            # Track response
            self.analytics.track_event(
                EventType.MESSAGE_RECEIVED,
                data={"length": len(response.content), "language": detected_lang.value},
                conversation_id=conversation_id,
                user_id=user_id
            )

            # Track metrics
            self.analytics.track_metric(
                MetricType.RESPONSE_TIME,
                value=response_time,
                conversation_id=conversation_id,
                tags={"language": detected_lang.value}
            )

            # Log response
            self.logger.info(
                "Response sent",
                response_time_ms=response_time,
                response_length=len(response.content)
            )

            # Check for performance issues
            if response_time > 2000:
                self.alerts.alert(
                    AlertLevel.WARNING,
                    "High Response Time",
                    f"Response took {response_time:.0f}ms",
                    source="chatbot",
                    metadata={"response_time_ms": response_time, "threshold_ms": 2000}
                )

            return response.content

        except Exception as e:
            # Log error
            self.logger.error("Chat error", error=str(e), error_type=type(e).__name__)

            # Track error event
            self.analytics.track_event(
                EventType.ERROR,
                data={"error": str(e), "error_type": type(e).__name__},
                conversation_id=conversation_id
            )

            # Trigger alert
            self.alerts.alert(
                AlertLevel.ERROR,
                "Chat Error",
                f"Error processing message: {str(e)}",
                source="chatbot"
            )

            raise

    async def get_health(self) -> ComponentHealth:
        """Get system health status."""
        return await self.health.check_all()

    def get_stats(self) -> dict:
        """Get analytics statistics."""
        analytics_stats = self.analytics.get_statistics(hours=24)

        # Add metrics stats
        response_time_stats = self.metrics.get_stats(MetricType.RESPONSE_TIME, window_minutes=60)

        return {
            "analytics": analytics_stats,
            "response_time": response_time_stats,
            "storage": {
                "conversations": self.storage.count()
            },
            "alerts": {
                "active": len(self.alerts.get_active_alerts()),
                "total": len(self.alerts.alerts)
            }
        }


async def main():
    print("🚀 Production Chatbot with Full Observability\n")

    # Initialize production chatbot
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, using demo mode")
        return

    bot = ProductionChatbot(api_key=api_key)

    # Example 1: Multi-language conversations
    print("=" * 60)
    print("Example 1: Multi-language Conversations")
    print("=" * 60)

    conversations = [
        ("Hello! How are you?", "en"),
        ("Ciao! Come stai?", "it"),
        ("¿Cómo estás?", "es"),
    ]

    for message, lang_code in conversations:
        print(f"\n[{lang_code}] User: {message}")
        response = await bot.chat(message, user_id="demo-user")
        print(f"[{lang_code}] Bot: {response[:150]}...")

    # Example 2: Check health
    print("\n" + "=" * 60)
    print("Example 2: Health Check")
    print("=" * 60)

    health = await bot.get_health()
    print(f"\nSystem Status: {health.status.value.upper()}")
    print(f"Message: {health.message}")

    for component in health.metadata["components"]:
        icon = "✅" if component["status"] == "healthy" else "❌"
        print(f"  {icon} {component['name']}: {component['message']}")

    # Example 3: View statistics
    print("\n" + "=" * 60)
    print("Example 3: Analytics Statistics")
    print("=" * 60)

    stats = bot.get_stats()

    print(f"\nAnalytics:")
    print(f"  Total events: {stats['analytics']['total_events']}")
    print(f"  Total metrics: {stats['analytics']['total_metrics']}")

    print(f"\nResponse Time (last hour):")
    print(f"  Count: {stats['response_time']['count']}")
    print(f"  Average: {stats['response_time']['avg']:.2f}ms")
    print(f"  Min: {stats['response_time']['min']:.2f}ms")
    print(f"  Max: {stats['response_time']['max']:.2f}ms")

    print(f"\nStorage:")
    print(f"  Conversations: {stats['storage']['conversations']}")

    print(f"\nAlerts:")
    print(f"  Active: {stats['alerts']['active']}")
    print(f"  Total: {stats['alerts']['total']}")

    # Example 4: View event history
    print("\n" + "=" * 60)
    print("Example 4: Event History")
    print("=" * 60)

    events = bot.analytics.get_events(limit=10)
    print(f"\nLast {len(events)} events:")

    for event in events[-5:]:
        print(f"\n  [{event.type.value}]")
        print(f"  Time: {event.timestamp.strftime('%H:%M:%S')}")
        if event.data:
            print(f"  Data: {event.data}")

    # Example 5: View alerts
    print("\n" + "=" * 60)
    print("Example 5: Active Alerts")
    print("=" * 60)

    active_alerts = bot.alerts.get_active_alerts()
    print(f"\nActive alerts: {len(active_alerts)}")

    for alert in active_alerts:
        icon = {"warning": "⚠️", "error": "❌", "critical": "🚨"}.get(alert.level.value, "ℹ️")
        print(f"\n  {icon} [{alert.level.value.upper()}] {alert.title}")
        print(f"  {alert.message}")
        print(f"  Source: {alert.source}")

    # Example 6: Export data
    print("\n" + "=" * 60)
    print("Example 6: Data Export")
    print("=" * 60)

    export_data = bot.analytics.export_data()
    print(f"\nExportable data:")
    print(f"  Events: {len(export_data['events'])}")
    print(f"  Metrics: {len(export_data['metrics'])}")

    # Save analytics (optional)
    # import json
    # with open("production_analytics.json", "w") as f:
    #     json.dump(export_data, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("Production Example Complete")
    print("=" * 60)

    print(f"\n✅ Successfully demonstrated:")
    print(f"  • Multi-language support with auto-detection")
    print(f"  • Event and metrics tracking")
    print(f"  • Health monitoring")
    print(f"  • Alert management")
    print(f"  • Performance monitoring")
    print(f"  • Data export")


if __name__ == "__main__":
    asyncio.run(main())
