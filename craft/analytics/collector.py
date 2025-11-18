"""Metrics collection and aggregation."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import time

from craft.analytics.tracker import Metric, MetricType


class MetricsCollector:
    """
    Collects and aggregates metrics over time windows.

    Provides real-time metrics aggregation and time-series data.

    Examples:
        collector = MetricsCollector()

        # Record metrics
        collector.record(MetricType.RESPONSE_TIME, 0.5, tags={"provider": "anthropic"})
        collector.record(MetricType.TOKENS_USED, 100)

        # Get aggregated metrics
        stats = collector.get_stats(MetricType.RESPONSE_TIME, window_minutes=5)
        print(f"Avg response time: {stats['avg']}ms")
    """

    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector.

        Args:
            retention_hours: How long to retain metrics (hours)
        """
        self.retention_hours = retention_hours
        self._metrics: List[Metric] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)

    def record(
        self,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric.

        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags
        """
        metric = Metric(type=metric_type, value=value, tags=tags or {})
        self._metrics.append(metric)

        # Update counters
        counter_key = f"{metric_type.value}:{self._tags_to_key(tags or {})}"
        self._counters[counter_key] += 1

        # Update timers for timing metrics
        if metric_type in {MetricType.RESPONSE_TIME}:
            timer_key = counter_key
            self._timers[timer_key].append(value)
            # Keep only last 1000 values
            if len(self._timers[timer_key]) > 1000:
                self._timers[timer_key] = self._timers[timer_key][-1000:]

        # Cleanup old metrics
        self._cleanup()

    def _tags_to_key(self, tags: Dict[str, str]) -> str:
        """Convert tags to string key."""
        if not tags:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(tags.items()))

    def _cleanup(self) -> None:
        """Remove metrics older than retention period."""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        self._metrics = [m for m in self._metrics if m.timestamp > cutoff]

    def get_stats(
        self,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        window_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Get statistics for a metric type.

        Args:
            metric_type: Type of metric
            tags: Optional filter by tags
            window_minutes: Time window in minutes

        Returns:
            Statistics dictionary
        """
        cutoff = datetime.now() - timedelta(minutes=window_minutes)

        # Filter metrics
        filtered = [
            m for m in self._metrics
            if m.type == metric_type and m.timestamp > cutoff
        ]

        if tags:
            filtered = [
                m for m in filtered
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]

        if not filtered:
            return {
                "count": 0,
                "sum": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "window_minutes": window_minutes,
            }

        values = [m.value for m in filtered]

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "window_minutes": window_minutes,
            "latest": values[-1] if values else 0,
        }

    def get_count(
        self,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
    ) -> int:
        """Get total count for a metric type."""
        key = f"{metric_type.value}:{self._tags_to_key(tags or {})}"
        return self._counters.get(key, 0)

    def get_rate(
        self,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        window_minutes: int = 1,
    ) -> float:
        """
        Get rate (count per minute) for a metric type.

        Args:
            metric_type: Type of metric
            tags: Optional filter by tags
            window_minutes: Time window in minutes

        Returns:
            Rate (events per minute)
        """
        stats = self.get_stats(metric_type, tags, window_minutes)
        return stats["count"] / window_minutes if window_minutes > 0 else 0

    def get_percentile(
        self,
        metric_type: MetricType,
        percentile: int,
        tags: Optional[Dict[str, str]] = None,
        window_minutes: int = 5,
    ) -> float:
        """
        Get percentile value for a metric.

        Args:
            metric_type: Type of metric
            percentile: Percentile (0-100)
            tags: Optional filter by tags
            window_minutes: Time window

        Returns:
            Percentile value
        """
        cutoff = datetime.now() - timedelta(minutes=window_minutes)

        filtered = [
            m for m in self._metrics
            if m.type == metric_type and m.timestamp > cutoff
        ]

        if tags:
            filtered = [
                m for m in filtered
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]

        if not filtered:
            return 0

        values = sorted([m.value for m in filtered])
        index = int(len(values) * (percentile / 100))
        return values[min(index, len(values) - 1)]

    def get_timeseries(
        self,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        window_minutes: int = 60,
        bucket_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get time-series data bucketed by time.

        Args:
            metric_type: Type of metric
            tags: Optional filter by tags
            window_minutes: Total time window
            bucket_minutes: Bucket size

        Returns:
            List of time buckets with statistics
        """
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        bucket_size = timedelta(minutes=bucket_minutes)

        # Filter metrics
        filtered = [
            m for m in self._metrics
            if m.type == metric_type and m.timestamp > cutoff
        ]

        if tags:
            filtered = [
                m for m in filtered
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]

        # Group into buckets
        buckets: Dict[datetime, List[float]] = defaultdict(list)

        for metric in filtered:
            bucket_time = metric.timestamp - timedelta(
                minutes=metric.timestamp.minute % bucket_minutes,
                seconds=metric.timestamp.second,
                microseconds=metric.timestamp.microsecond
            )
            buckets[bucket_time].append(metric.value)

        # Create time series
        timeseries = []
        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]
            timeseries.append({
                "timestamp": bucket_time.isoformat(),
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            })

        return timeseries

    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._counters.clear()
        self._timers.clear()


class Timer:
    """
    Context manager for timing operations.

    Examples:
        collector = MetricsCollector()

        with Timer(collector, MetricType.RESPONSE_TIME, tags={"provider": "anthropic"}):
            # Your code here
            response = chatbot.chat("Hello")
    """

    def __init__(
        self,
        collector: MetricsCollector,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize timer.

        Args:
            collector: Metrics collector
            metric_type: Type of metric to record
            tags: Optional tags
        """
        self.collector = collector
        self.metric_type = metric_type
        self.tags = tags
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record metric."""
        if self.start_time is not None:
            elapsed = (time.time() - self.start_time) * 1000  # Convert to ms
            self.collector.record(self.metric_type, elapsed, self.tags)
