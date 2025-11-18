"""Tests for analytics module."""

import pytest
from datetime import datetime

from craft.analytics import (
    AnalyticsTracker,
    EventType,
    MetricType,
    MetricsCollector,
    Timer,
)


@pytest.mark.unit
class TestAnalyticsTracker:
    """Test AnalyticsTracker class."""

    def test_create_tracker(self):
        """Test creating analytics tracker."""
        tracker = AnalyticsTracker()

        assert len(tracker.events) == 0
        assert len(tracker.metrics) == 0
        assert tracker.is_enabled is True

    def test_track_event(self):
        """Test tracking an event."""
        tracker = AnalyticsTracker()

        event = tracker.track_event(
            EventType.MESSAGE_SENT,
            data={"message": "Hello"},
            conversation_id="conv-123"
        )

        assert len(tracker.events) == 1
        assert event.type == EventType.MESSAGE_SENT
        assert event.data["message"] == "Hello"
        assert event.conversation_id == "conv-123"

    def test_track_metric(self):
        """Test tracking a metric."""
        tracker = AnalyticsTracker()

        metric = tracker.track_metric(
            MetricType.RESPONSE_TIME,
            value=250.5,
            tags={"provider": "anthropic"}
        )

        assert len(tracker.metrics) == 1
        assert metric.type == MetricType.RESPONSE_TIME
        assert metric.value == 250.5
        assert metric.tags["provider"] == "anthropic"

    def test_get_events(self):
        """Test getting events."""
        tracker = AnalyticsTracker()

        tracker.track_event(EventType.MESSAGE_SENT)
        tracker.track_event(EventType.MESSAGE_RECEIVED)
        tracker.track_event(EventType.MESSAGE_SENT)

        events = tracker.get_events(event_type=EventType.MESSAGE_SENT)
        assert len(events) == 2

    def test_get_metrics(self):
        """Test getting metrics."""
        tracker = AnalyticsTracker()

        tracker.track_metric(MetricType.RESPONSE_TIME, 100)
        tracker.track_metric(MetricType.RESPONSE_TIME, 200)
        tracker.track_metric(MetricType.TOKENS_USED, 50)

        metrics = tracker.get_metrics(metric_type=MetricType.RESPONSE_TIME)
        assert len(metrics) == 2

    def test_get_statistics(self):
        """Test getting statistics."""
        tracker = AnalyticsTracker()

        tracker.track_event(EventType.MESSAGE_SENT, conversation_id="conv-1")
        tracker.track_event(EventType.MESSAGE_SENT, conversation_id="conv-2")
        tracker.track_metric(MetricType.RESPONSE_TIME, 250)

        stats = tracker.get_statistics(hours=24)

        assert stats["total_events"] == 2
        assert stats["total_metrics"] == 1
        assert stats["unique_conversations"] == 2

    def test_export_data(self):
        """Test exporting analytics data."""
        tracker = AnalyticsTracker()

        tracker.track_event(EventType.MESSAGE_SENT)
        tracker.track_metric(MetricType.RESPONSE_TIME, 100)

        exported = tracker.export_data()

        assert "events" in exported
        assert "metrics" in exported
        assert "statistics" in exported
        assert len(exported["events"]) == 1
        assert len(exported["metrics"]) == 1

    def test_clear(self):
        """Test clearing analytics data."""
        tracker = AnalyticsTracker()

        tracker.track_event(EventType.MESSAGE_SENT)
        tracker.track_metric(MetricType.RESPONSE_TIME, 100)

        tracker.clear()

        assert len(tracker.events) == 0
        assert len(tracker.metrics) == 0

    def test_disable_enable(self):
        """Test disabling and enabling tracking."""
        tracker = AnalyticsTracker()

        tracker.disable()
        assert tracker.is_enabled is False

        tracker.track_event(EventType.MESSAGE_SENT)
        assert len(tracker.events) == 0  # Should not track when disabled

        tracker.enable()
        assert tracker.is_enabled is True

        tracker.track_event(EventType.MESSAGE_SENT)
        assert len(tracker.events) == 1  # Should track when enabled

    def test_max_events_limit(self):
        """Test that old events are trimmed."""
        tracker = AnalyticsTracker(max_events=5)

        for i in range(10):
            tracker.track_event(EventType.MESSAGE_SENT)

        assert len(tracker.events) == 5  # Should only keep last 5


@pytest.mark.unit
class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_create_collector(self):
        """Test creating metrics collector."""
        collector = MetricsCollector()

        assert collector.retention_hours == 24

    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()

        collector.record(MetricType.RESPONSE_TIME, 250.5)
        collector.record(MetricType.RESPONSE_TIME, 150.0)

        stats = collector.get_stats(MetricType.RESPONSE_TIME, window_minutes=5)

        assert stats["count"] == 2
        assert stats["avg"] == (250.5 + 150.0) / 2

    def test_get_stats(self):
        """Test getting metric statistics."""
        collector = MetricsCollector()

        collector.record(MetricType.RESPONSE_TIME, 100)
        collector.record(MetricType.RESPONSE_TIME, 200)
        collector.record(MetricType.RESPONSE_TIME, 300)

        stats = collector.get_stats(MetricType.RESPONSE_TIME, window_minutes=5)

        assert stats["count"] == 3
        assert stats["avg"] == 200
        assert stats["min"] == 100
        assert stats["max"] == 300

    def test_get_percentile(self):
        """Test getting percentile."""
        collector = MetricsCollector()

        for i in range(100):
            collector.record(MetricType.RESPONSE_TIME, i)

        p50 = collector.get_percentile(MetricType.RESPONSE_TIME, 50, window_minutes=5)
        p95 = collector.get_percentile(MetricType.RESPONSE_TIME, 95, window_minutes=5)

        assert p50 < p95
        assert p50 >= 40  # Approximately 50th percentile
        assert p95 >= 90  # Approximately 95th percentile

    def test_get_rate(self):
        """Test getting metric rate."""
        collector = MetricsCollector()

        for i in range(10):
            collector.record(MetricType.API_CALLS, 1)

        rate = collector.get_rate(MetricType.API_CALLS, window_minutes=1)

        assert rate == 10  # 10 events per minute

    def test_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()

        collector.record(MetricType.RESPONSE_TIME, 100)
        collector.clear()

        stats = collector.get_stats(MetricType.RESPONSE_TIME, window_minutes=5)
        assert stats["count"] == 0


@pytest.mark.unit
class TestTimer:
    """Test Timer context manager."""

    def test_timer_records_metric(self):
        """Test that timer records a metric."""
        collector = MetricsCollector()

        import time
        with Timer(collector, MetricType.RESPONSE_TIME):
            time.sleep(0.01)  # Small delay

        stats = collector.get_stats(MetricType.RESPONSE_TIME, window_minutes=1)

        assert stats["count"] == 1
        assert stats["avg"] >= 10  # At least 10ms

    def test_timer_with_tags(self):
        """Test timer with tags."""
        collector = MetricsCollector()

        with Timer(collector, MetricType.RESPONSE_TIME, tags={"operation": "test"}):
            pass

        stats = collector.get_stats(
            MetricType.RESPONSE_TIME,
            tags={"operation": "test"},
            window_minutes=1
        )

        assert stats["count"] == 1
