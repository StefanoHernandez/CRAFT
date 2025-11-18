"""Alerting system for critical events."""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alert model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """
    Alert management system.

    Manages alerts, triggers notifications, and tracks alert history.

    Examples:
        alert_mgr = AlertManager()

        # Add alert handler
        def send_email(alert: Alert):
            print(f"Email alert: {alert.title}")

        alert_mgr.add_handler(AlertLevel.CRITICAL, send_email)

        # Trigger alert
        alert_mgr.alert(
            AlertLevel.CRITICAL,
            "System Down",
            "Database connection failed",
            source="database"
        )
    """

    def __init__(self, max_alerts: int = 1000):
        """
        Initialize alert manager.

        Args:
            max_alerts: Maximum alerts to keep in history
        """
        self.max_alerts = max_alerts
        self.alerts: List[Alert] = []
        self._handlers: Dict[AlertLevel, List[Callable]] = {
            level: [] for level in AlertLevel
        }

    def add_handler(self, level: AlertLevel, handler: Callable[[Alert], None]) -> None:
        """
        Add alert handler.

        Args:
            level: Minimum alert level to trigger handler
            handler: Function that receives Alert object
        """
        self._handlers[level].append(handler)

    def remove_handler(self, level: AlertLevel, handler: Callable) -> None:
        """Remove alert handler."""
        if handler in self._handlers[level]:
            self._handlers[level].remove(handler)

    def alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """
        Create and trigger an alert.

        Args:
            level: Alert severity level
            title: Alert title
            message: Alert message
            source: Optional source component
            metadata: Optional metadata

        Returns:
            Created alert
        """
        alert = Alert(
            level=level,
            title=title,
            message=message,
            source=source,
            metadata=metadata or {},
        )

        self.alerts.append(alert)

        # Trim if needed
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]

        # Trigger handlers
        self._trigger_handlers(alert)

        return alert

    def _trigger_handlers(self, alert: Alert) -> None:
        """Trigger registered handlers for an alert."""
        # Get severity levels >= alert level
        levels_to_trigger = []

        level_order = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
        alert_index = level_order.index(alert.level)

        for level in level_order[alert_index:]:
            levels_to_trigger.append(level)

        # Call handlers
        for level in levels_to_trigger:
            for handler in self._handlers[level]:
                try:
                    handler(alert)
                except Exception as e:
                    # Don't let handler errors crash the system
                    print(f"Alert handler error: {e}")

    def resolve(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.

        Args:
            alert_id: Alert ID

        Returns:
            True if alert was resolved
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                return True

        return False

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        Get active (unresolved) alerts.

        Args:
            level: Optional filter by level

        Returns:
            List of active alerts
        """
        alerts = [a for a in self.alerts if not a.resolved]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_history(
        self,
        level: Optional[AlertLevel] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            level: Optional filter by level
            hours: Hours to look back
            limit: Maximum alerts to return

        Returns:
            List of historical alerts
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)

        alerts = [a for a in self.alerts if a.timestamp > cutoff]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get alert statistics.

        Args:
            hours: Hours to analyze

        Returns:
            Statistics dictionary
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)

        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff]

        # Count by level
        by_level = {
            level.value: len([a for a in recent_alerts if a.level == level])
            for level in AlertLevel
        }

        # Count by source
        by_source: Dict[str, int] = {}
        for alert in recent_alerts:
            if alert.source:
                by_source[alert.source] = by_source.get(alert.source, 0) + 1

        # Count resolved vs active
        resolved = len([a for a in recent_alerts if a.resolved])
        active = len([a for a in recent_alerts if not a.resolved])

        return {
            "period_hours": hours,
            "total_alerts": len(recent_alerts),
            "by_level": by_level,
            "by_source": by_source,
            "resolved": resolved,
            "active": active,
        }

    def clear_resolved(self) -> int:
        """
        Clear resolved alerts from history.

        Returns:
            Number of alerts cleared
        """
        before = len(self.alerts)
        self.alerts = [a for a in self.alerts if not a.resolved]
        return before - len(self.alerts)

    def clear_all(self) -> None:
        """Clear all alerts."""
        self.alerts.clear()


# Pre-defined alert handlers

def console_alert_handler(alert: Alert) -> None:
    """Print alert to console."""
    icon = {
        AlertLevel.INFO: "ℹ️",
        AlertLevel.WARNING: "⚠️",
        AlertLevel.ERROR: "❌",
        AlertLevel.CRITICAL: "🚨",
    }.get(alert.level, "")

    print(f"\n{icon} [{alert.level.value.upper()}] {alert.title}")
    print(f"   {alert.message}")
    if alert.source:
        print(f"   Source: {alert.source}")
    print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def log_alert_handler(logger) -> Callable[[Alert], None]:
    """Create alert handler that logs to a logger."""
    def handler(alert: Alert):
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }.get(alert.level, logger.info)

        log_method(
            f"ALERT: {alert.title}",
            message=alert.message,
            source=alert.source,
            alert_id=alert.id,
        )

    return handler
