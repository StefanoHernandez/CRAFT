"""
Analytics & Metrics Example

Demonstrates CRAFT's analytics and metrics tracking system.
"""

from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.analytics import AnalyticsTracker, EventType, MetricType, MetricsCollector, Timer
import os
import time
import asyncio


async def main():
    print("📊 Analytics & Metrics Example\n")

    # Initialize tracking
    tracker = AnalyticsTracker()
    collector = MetricsCollector()

    # Example 1: Track events
    print("=" * 60)
    print("Example 1: Event Tracking")
    print("=" * 60)

    # Track conversation events
    tracker.track_event(
        EventType.CONVERSATION_STARTED,
        data={"user": "alice"},
        conversation_id="conv-123"
    )

    tracker.track_event(
        EventType.MESSAGE_SENT,
        data={"message": "Hello", "length": 5},
        conversation_id="conv-123"
    )

    tracker.track_event(
        EventType.MESSAGE_RECEIVED,
        data={"message": "Hi there!", "length": 9},
        conversation_id="conv-123"
    )

    print(f"Tracked {len(tracker.events)} events")

    # Example 2: Track metrics
    print("\n" + "=" * 60)
    print("Example 2: Metrics Tracking")
    print("=" * 60)

    # Simulate some metrics
    for i in range(10):
        # Response time metric
        response_time = 200 + (i * 50)  # ms
        tracker.track_metric(
            MetricType.RESPONSE_TIME,
            value=response_time,
            tags={"provider": "anthropic"}
        )

        collector.record(
            MetricType.RESPONSE_TIME,
            value=response_time,
            tags={"provider": "anthropic"}
        )

        # Tokens used
        tracker.track_metric(
            MetricType.TOKENS_USED,
            value=100 + (i * 10),
            tags={"model": "claude-3-5-sonnet"}
        )

    print("Recorded response time and token metrics")

    # Example 3: Get statistics
    print("\n" + "=" * 60)
    print("Example 3: Statistics")
    print("=" * 60)

    stats = tracker.get_statistics(hours=24)
    print(f"\nStatistics (last 24 hours):")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Total metrics: {stats['total_metrics']}")
    print(f"  Unique conversations: {stats['unique_conversations']}")

    print(f"\n Event counts:")
    for event_type, count in stats['event_counts'].items():
        print(f"    {event_type}: {count}")

    print(f"\n Metric stats:")
    for metric_type, metric_stats in stats['metric_stats'].items():
        print(f"    {metric_type}:")
        print(f"      Count: {metric_stats['count']}")
        print(f"      Avg: {metric_stats['avg']:.2f}")
        print(f"      Min: {metric_stats['min']:.2f}")
        print(f"      Max: {metric_stats['max']:.2f}")

    # Example 4: Metrics collector advanced features
    print("\n" + "=" * 60)
    print("Example 4: Metrics Collector")
    print("=" * 60)

    # Get aggregated stats
    response_stats = collector.get_stats(
        MetricType.RESPONSE_TIME,
        tags={"provider": "anthropic"},
        window_minutes=5
    )

    print(f"\nResponse time stats (last 5 min):")
    print(f"  Count: {response_stats['count']}")
    print(f"  Average: {response_stats['avg']:.2f}ms")
    print(f"  Min: {response_stats['min']:.2f}ms")
    print(f"  Max: {response_stats['max']:.2f}ms")
    print(f"  Latest: {response_stats['latest']:.2f}ms")

    # Get percentiles
    p50 = collector.get_percentile(MetricType.RESPONSE_TIME, 50, window_minutes=5)
    p95 = collector.get_percentile(MetricType.RESPONSE_TIME, 95, window_minutes=5)
    p99 = collector.get_percentile(MetricType.RESPONSE_TIME, 99, window_minutes=5)

    print(f"\n Percentiles:")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    # Example 5: Timer context manager
    print("\n" + "=" * 60)
    print("Example 5: Timer for Operations")
    print("=" * 60)

    with Timer(collector, MetricType.RESPONSE_TIME, tags={"operation": "chat"}):
        # Simulate a chat operation
        time.sleep(0.2)
        print("  Chat operation completed")

    with Timer(collector, MetricType.RESPONSE_TIME, tags={"operation": "rag"}):
        # Simulate RAG retrieval
        time.sleep(0.1)
        print("  RAG retrieval completed")

    # Get stats for each operation
    chat_stats = collector.get_stats(
        MetricType.RESPONSE_TIME,
        tags={"operation": "chat"},
        window_minutes=1
    )
    rag_stats = collector.get_stats(
        MetricType.RESPONSE_TIME,
        tags={"operation": "rag"},
        window_minutes=1
    )

    print(f"\n Operation timings:")
    print(f"  Chat: {chat_stats['avg']:.2f}ms")
    print(f"  RAG: {rag_stats['avg']:.2f}ms")

    # Example 6: Real chatbot with analytics
    print("\n" + "=" * 60)
    print("Example 6: Chatbot with Analytics")
    print("=" * 60)

    chatbot = Chatbot(
        provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    )

    conversation_id = chatbot.conversation.id

    # Track conversation start
    tracker.track_event(
        EventType.CONVERSATION_STARTED,
        conversation_id=conversation_id
    )

    # Chat with tracking
    print("\n  Sending message...")
    start_time = time.time()

    tracker.track_event(
        EventType.MESSAGE_SENT,
        data={"message": "What is machine learning?"},
        conversation_id=conversation_id
    )

    response = chatbot.chat("What is machine learning?")

    # Calculate response time
    response_time = (time.time() - start_time) * 1000

    tracker.track_event(
        EventType.MESSAGE_RECEIVED,
        data={"message": response.content[:100], "length": len(response.content)},
        conversation_id=conversation_id
    )

    tracker.track_metric(
        MetricType.RESPONSE_TIME,
        value=response_time,
        conversation_id=conversation_id,
        tags={"provider": "anthropic"}
    )

    print(f"  Response time: {response_time:.2f}ms")
    print(f"  Response length: {len(response.content)} chars")

    # Example 7: Export analytics
    print("\n" + "=" * 60)
    print("Example 7: Export Analytics Data")
    print("=" * 60)

    export_data = tracker.export_data()
    print(f"\nExported data:")
    print(f"  Events: {len(export_data['events'])}")
    print(f"  Metrics: {len(export_data['metrics'])}")
    print(f"  Statistics: {list(export_data['statistics'].keys())}")

    # Save to file (optional)
    # import json
    # with open("analytics.json", "w") as f:
    #     json.dump(export_data, f, indent=2, default=str)


if __name__ == "__main__":
    asyncio.run(main())
