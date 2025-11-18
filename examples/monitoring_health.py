"""
Monitoring & Health Checks Example

Demonstrates CRAFT's monitoring, health checks, and alerting system.
"""

from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.storage import SQLiteStorage
from craft.monitoring import (
    HealthCheck,
    HealthStatus,
    ComponentHealth,
    AdvancedLogger,
    LogLevel,
    AlertManager,
    AlertLevel,
    console_alert_handler,
    log_alert_handler,
)
import os
import asyncio
import time


async def main():
    print("🏥 Monitoring & Health Checks Example\n")

    # Example 1: Advanced logging
    print("=" * 60)
    print("Example 1: Advanced Structured Logging")
    print("=" * 60)

    # Create logger
    logger = AdvancedLogger("craft-app", level=LogLevel.INFO)

    logger.info("Application started")
    logger.info("User action", user_id="123", action="login")
    logger.warning("High memory usage", percent=85)
    logger.error("Failed to connect", service="database", retry=3)

    # With context
    request_logger = logger.with_context(request_id="req-456", user_id="789")
    request_logger.info("Processing request")
    request_logger.info("Request completed", duration_ms=250)

    # JSON logging
    print("\nJSON Logging:")
    json_logger = AdvancedLogger("craft-json", json_logs=True)
    json_logger.info("Event occurred", event_type="user_signup", user_id="new-123")

    # Example 2: Health checks
    print("\n" + "=" * 60)
    print("Example 2: Health Check System")
    print("=" * 60)

    health = HealthCheck()

    # Add component checks

    async def check_provider() -> ComponentHealth:
        """Check provider health."""
        try:
            # Simulate provider check
            await asyncio.sleep(0.1)
            return ComponentHealth(
                name="provider",
                status=HealthStatus.HEALTHY,
                message="Anthropic provider operational",
                metadata={"latency_ms": 100}
            )
        except Exception as e:
            return ComponentHealth(
                name="provider",
                status=HealthStatus.UNHEALTHY,
                message=f"Provider error: {str(e)}"
            )

    async def check_storage() -> ComponentHealth:
        """Check storage health."""
        try:
            storage = SQLiteStorage(database_path=":memory:")
            count = storage.count()
            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                message=f"Storage operational ({count} conversations)",
                metadata={"count": count}
            )
        except Exception as e:
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage error: {str(e)}"
            )

    async def check_memory() -> ComponentHealth:
        """Check memory usage."""
        # Simulated memory check
        memory_percent = 65  # Simulated

        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = "Critical memory usage"
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
            message = "High memory usage"
        else:
            status = HealthStatus.HEALTHY
            message = "Memory usage normal"

        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            metadata={"percent": memory_percent}
        )

    # Register checks
    health.add_check("provider", check_provider)
    health.add_check("storage", check_storage)
    health.add_check("memory", check_memory)

    # Run checks
    print("\nRunning health checks...")
    overall_health = await health.check_all()

    print(f"\nOverall Status: {overall_health.status.value.upper()}")
    print(f"Message: {overall_health.message}")

    print(f"\nComponent Status:")
    for component in overall_health.metadata["components"]:
        icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }.get(component["status"], "")

        print(f"  {icon} {component['name']}: {component['status']} - {component['message']}")

    # Check individual component
    provider_health = await health.check_component("provider")
    print(f"\nProvider Health: {provider_health.status.value}")

    # Check if system is healthy
    print(f"\nSystem Healthy: {health.is_healthy()}")

    # Example 3: Alert management
    print("\n" + "=" * 60)
    print("Example 3: Alert Management")
    print("=" * 60)

    alert_mgr = AlertManager()

    # Add alert handlers
    alert_mgr.add_handler(AlertLevel.WARNING, console_alert_handler)
    alert_mgr.add_handler(AlertLevel.CRITICAL, log_alert_handler(logger))

    # Trigger alerts
    print("\nTriggering alerts...\n")

    alert_mgr.alert(
        AlertLevel.INFO,
        "System Update",
        "New version deployed successfully",
        source="deployment"
    )

    alert_mgr.alert(
        AlertLevel.WARNING,
        "High Latency",
        "Response time increased to 2s",
        source="provider",
        metadata={"latency_ms": 2000, "threshold_ms": 1000}
    )

    alert_mgr.alert(
        AlertLevel.ERROR,
        "Storage Full",
        "Database storage at 95% capacity",
        source="storage",
        metadata={"used_gb": 95, "total_gb": 100}
    )

    alert_mgr.alert(
        AlertLevel.CRITICAL,
        "Service Down",
        "Provider API is not responding",
        source="provider",
        metadata={"last_success": "2024-01-20 14:30:00"}
    )

    # Get active alerts
    print("\n" + "=" * 60)
    print("Active Alerts")
    print("=" * 60)

    active_alerts = alert_mgr.get_active_alerts()
    print(f"\nActive alerts: {len(active_alerts)}")

    for alert in active_alerts:
        print(f"\n  [{alert.level.value.upper()}] {alert.title}")
        print(f"  Message: {alert.message}")
        print(f"  Source: {alert.source}")
        print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Alert statistics
    stats = alert_mgr.get_alert_stats(hours=1)
    print(f"\n" + "=" * 60)
    print("Alert Statistics (last hour)")
    print("=" * 60)

    print(f"\nTotal alerts: {stats['total_alerts']}")
    print(f"Active: {stats['active']}")
    print(f"Resolved: {stats['resolved']}")

    print(f"\nBy level:")
    for level, count in stats['by_level'].items():
        if count > 0:
            print(f"  {level}: {count}")

    print(f"\nBy source:")
    for source, count in stats['by_source'].items():
        print(f"  {source}: {count}")

    # Resolve an alert
    if active_alerts:
        first_alert = active_alerts[0]
        alert_mgr.resolve(first_alert.id)
        print(f"\nResolved alert: {first_alert.title}")

    # Example 4: Complete monitoring setup
    print("\n" + "=" * 60)
    print("Example 4: Complete Monitoring Setup")
    print("=" * 60)

    # Setup logging
    app_logger = AdvancedLogger("craft-production", level=LogLevel.INFO)

    # Setup health checks
    app_health = HealthCheck()
    app_health.add_check("provider", check_provider)
    app_health.add_check("storage", check_storage)

    # Setup alerts
    app_alerts = AlertManager()
    app_alerts.add_handler(AlertLevel.ERROR, console_alert_handler)
    app_alerts.add_handler(AlertLevel.CRITICAL, log_alert_handler(app_logger))

    # Monitoring loop simulation
    print("\nSimulating monitoring loop...")

    for i in range(3):
        print(f"\n--- Check {i + 1} ---")

        # Run health checks
        health_result = await app_health.check_all()
        app_logger.info(
            "Health check completed",
            status=health_result.status.value,
            components=len(health_result.metadata["components"])
        )

        # Trigger alert if unhealthy
        if health_result.status != HealthStatus.HEALTHY:
            app_alerts.alert(
                AlertLevel.WARNING if health_result.status == HealthStatus.DEGRADED else AlertLevel.ERROR,
                "Health Check Failed",
                health_result.message,
                source="health_monitor"
            )

        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("Monitoring Example Complete")
    print("=" * 60)

    # Summary
    print(f"\nSummary:")
    print(f"  Health status: {health_result.status.value}")
    print(f"  Total alerts: {len(app_alerts.alerts)}")
    print(f"  Active alerts: {len(app_alerts.get_active_alerts())}")


if __name__ == "__main__":
    asyncio.run(main())
