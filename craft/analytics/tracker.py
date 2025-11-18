"""Analytics and event tracking."""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types of tracked events."""

    # Conversation events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"

    # Provider events
    PROVIDER_REQUEST = "provider_request"
    PROVIDER_RESPONSE = "provider_response"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_STREAM_START = "provider_stream_start"
    PROVIDER_STREAM_END = "provider_stream_end"

    # RAG events
    RAG_QUERY = "rag_query"
    RAG_RETRIEVAL = "rag_retrieval"
    RAG_DOCUMENTS_ADDED = "rag_documents_added"

    # Storage events
    STORAGE_SAVE = "storage_save"
    STORAGE_LOAD = "storage_load"
    STORAGE_DELETE = "storage_delete"

    # API events
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    API_ERROR = "api_error"

    # System events
    ERROR = "error"
    WARNING = "warning"


class MetricType(str, Enum):
    """Types of metrics."""

    # Performance metrics
    RESPONSE_TIME = "response_time"
    TOKENS_USED = "tokens_used"
    TOKENS_PER_SECOND = "tokens_per_second"

    # Usage metrics
    MESSAGES_COUNT = "messages_count"
    CONVERSATIONS_COUNT = "conversations_count"
    USERS_COUNT = "users_count"
    API_CALLS = "api_calls"

    # Quality metrics
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    AVERAGE_RESPONSE_LENGTH = "average_response_length"

    # RAG metrics
    RETRIEVAL_SCORE = "retrieval_score"
    DOCUMENTS_RETRIEVED = "documents_retrieved"

    # Cost metrics
    COST_USD = "cost_usd"


class Event(BaseModel):
    """Tracked event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    provider: Optional[str] = None


class Metric(BaseModel):
    """Tracked metric."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: Dict[str, str] = Field(default_factory=dict)
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class AnalyticsTracker:
    """
    Analytics and metrics tracking system.

    Tracks events, metrics, and usage patterns for monitoring and optimization.

    Examples:
        tracker = AnalyticsTracker()

        # Track event
        tracker.track_event(
            EventType.MESSAGE_SENT,
            data={"message": "Hello"},
            conversation_id="123"
        )

        # Track metric
        tracker.track_metric(
            MetricType.RESPONSE_TIME,
            value=0.5,
            tags={"provider": "anthropic"}
        )

        # Get statistics
        stats = tracker.get_statistics(hours=24)
    """

    def __init__(self, max_events: int = 10000, max_metrics: int = 10000):
        """
        Initialize analytics tracker.

        Args:
            max_events: Maximum events to keep in memory
            max_metrics: Maximum metrics to keep in memory
        """
        self.max_events = max_events
        self.max_metrics = max_metrics
        self.events: List[Event] = []
        self.metrics: List[Metric] = []
        self._enabled = True

    def track_event(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Event:
        """
        Track an event.

        Args:
            event_type: Type of event
            data: Event data
            user_id: Optional user ID
            conversation_id: Optional conversation ID
            provider: Optional provider name

        Returns:
            Created event
        """
        if not self._enabled:
            return Event(type=event_type)

        event = Event(
            type=event_type,
            data=data or {},
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
        )

        self.events.append(event)

        # Trim if needed
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        return event

    def track_metric(
        self,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Metric:
        """
        Track a metric.

        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags
            user_id: Optional user ID
            conversation_id: Optional conversation ID

        Returns:
            Created metric
        """
        if not self._enabled:
            return Metric(type=metric_type, value=value)

        metric = Metric(
            type=metric_type,
            value=value,
            tags=tags or {},
            user_id=user_id,
            conversation_id=conversation_id,
        )

        self.metrics.append(metric)

        # Trim if needed
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics :]

        return metric

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        conversation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get events with optional filtering."""
        filtered = self.events

        if event_type:
            filtered = [e for e in filtered if e.type == event_type]

        if conversation_id:
            filtered = [e for e in filtered if e.conversation_id == conversation_id]

        return filtered[-limit:]

    def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        tags: Optional[Dict[str, str]] = None,
        limit: int = 100,
    ) -> List[Metric]:
        """Get metrics with optional filtering."""
        filtered = self.metrics

        if metric_type:
            filtered = [m for m in filtered if m.type == metric_type]

        if tags:
            filtered = [
                m for m in filtered
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]

        return filtered[-limit:]

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics for the last N hours.

        Args:
            hours: Number of hours to analyze

        Returns:
            Statistics dictionary
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)

        recent_events = [e for e in self.events if e.timestamp.timestamp() > cutoff]
        recent_metrics = [m for m in self.metrics if m.timestamp.timestamp() > cutoff]

        # Count events by type
        event_counts = {}
        for event in recent_events:
            event_counts[event.type.value] = event_counts.get(event.type.value, 0) + 1

        # Calculate metric statistics
        metric_stats = {}
        for metric_type in MetricType:
            type_metrics = [m for m in recent_metrics if m.type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                metric_stats[metric_type.value] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }

        # Count unique conversations and users
        unique_conversations = len(set(e.conversation_id for e in recent_events if e.conversation_id))
        unique_users = len(set(e.user_id for e in recent_events if e.user_id))

        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "total_metrics": len(recent_metrics),
            "event_counts": event_counts,
            "metric_stats": metric_stats,
            "unique_conversations": unique_conversations,
            "unique_users": unique_users,
        }

    def export_data(self) -> Dict[str, Any]:
        """Export all analytics data."""
        return {
            "events": [e.model_dump() for e in self.events],
            "metrics": [m.model_dump() for m in self.metrics],
            "statistics": self.get_statistics(),
        }

    def clear(self) -> None:
        """Clear all tracked data."""
        self.events.clear()
        self.metrics.clear()

    def enable(self) -> None:
        """Enable tracking."""
        self._enabled = True

    def disable(self) -> None:
        """Disable tracking."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if tracking is enabled."""
        return self._enabled

    def __repr__(self) -> str:
        return f"AnalyticsTracker(events={len(self.events)}, metrics={len(self.metrics)})"
