# Advanced Features Guide (Phase 6)

CRAFT provides advanced features for production deployments including multi-language support, analytics, monitoring, and alerting.

## Multi-Language Support (i18n)

### Overview

CRAFT includes built-in internationalization (i18n) support for creating multi-language chatbots.

**Features:**
- Auto-detect user language
- 10 supported languages (EN, IT, ES, FR, DE, PT, ZH, JA, KO, RU)
- Translated system messages
- Language-specific prompts

### Basic Usage

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.i18n import Translator, Language, detect_language

# Create translator
translator = Translator(language=Language.ITALIAN)

# Get translated messages
print(translator.get("welcome"))  # "Benvenuto in CRAFT"
print(translator.get("error"))     # "Si è verificato un errore"

# Auto-detect language
user_message = "Ciao! Come stai?"
detected_lang = detect_language(user_message)  # Language.ITALIAN

# Create language-specific chatbot
translator = Translator(language=detected_lang)
lang_prompt = translator.translate_prompt("You are a helpful assistant.")

chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    system_prompt=lang_prompt
)
```

### Supported Languages

| Code | Language   | Example Detection Keywords |
|------|------------|----------------------------|
| en   | English    | hello, how are you        |
| it   | Italian    | ciao, grazie, come stai   |
| es   | Spanish    | hola, gracias, cómo estás |
| fr   | French     | bonjour, merci            |
| de   | German     | hallo, danke              |
| pt   | Portuguese | olá, obrigado             |
| zh   | Chinese    | (Chinese characters)      |
| ja   | Japanese   | (Japanese characters)     |
| ko   | Korean     | (Korean characters)       |
| ru   | Russian    | (Cyrillic characters)     |

### Translation Keys

Built-in translation keys:

```python
translator = Translator(language=Language.ITALIAN)

# System messages
translator.get("welcome")                 # "Benvenuto in CRAFT"
translator.get("goodbye")                 # "Arrivederci!"
translator.get("error")                   # "Si è verificato un errore"
translator.get("conversation_started")    # "Conversazione iniziata"
translator.get("message_sent")            # "Messaggio inviato"

# Error messages
translator.get("connection_error")        # "Errore di connessione"
translator.get("timeout_error")           # "Timeout della richiesta"
translator.get("rate_limit_error")        # "Limite di richieste superato"
translator.get("invalid_api_key")         # "Chiave API non valida"
```

### Auto-Detection Example

```python
def chat_multilingual(message: str):
    # Detect language
    lang = detect_language(message)
    translator = Translator(language=lang)

    # Create chatbot
    prompt = translator.translate_prompt("You are a helpful assistant.")
    chatbot = Chatbot(provider=provider, system_prompt=prompt)

    # Chat
    response = chatbot.chat(message)
    return response.content

# Works with any language!
chat_multilingual("Hello!")          # English response
chat_multilingual("Ciao!")           # Italian response
chat_multilingual("¡Hola!")          # Spanish response
```

---

## Analytics & Metrics

### Overview

Track events, metrics, and usage patterns for monitoring and optimization.

**Features:**
- Event tracking (conversations, messages, errors)
- Metrics collection (response time, tokens, quality)
- Real-time statistics
- Time-series data
- Export capabilities

### Analytics Tracker

```python
from craft.analytics import AnalyticsTracker, EventType, MetricType

# Create tracker
tracker = AnalyticsTracker()

# Track events
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

# Track metrics
tracker.track_metric(
    MetricType.RESPONSE_TIME,
    value=250.5,  # milliseconds
    tags={"provider": "anthropic"}
)

tracker.track_metric(
    MetricType.TOKENS_USED,
    value=150,
    tags={"model": "claude-3-5-sonnet"}
)

# Get statistics
stats = tracker.get_statistics(hours=24)
print(f"Total events: {stats['total_events']}")
print(f"Unique conversations: {stats['unique_conversations']}")
```

### Event Types

```python
class EventType(Enum):
    # Conversation
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"

    # Provider
    PROVIDER_REQUEST = "provider_request"
    PROVIDER_RESPONSE = "provider_response"
    PROVIDER_ERROR = "provider_error"

    # RAG
    RAG_QUERY = "rag_query"
    RAG_RETRIEVAL = "rag_retrieval"
    RAG_DOCUMENTS_ADDED = "rag_documents_added"

    # Storage
    STORAGE_SAVE = "storage_save"
    STORAGE_LOAD = "storage_load"

    # System
    ERROR = "error"
    WARNING = "warning"
```

### Metric Types

```python
class MetricType(Enum):
    # Performance
    RESPONSE_TIME = "response_time"
    TOKENS_USED = "tokens_used"
    TOKENS_PER_SECOND = "tokens_per_second"

    # Usage
    MESSAGES_COUNT = "messages_count"
    CONVERSATIONS_COUNT = "conversations_count"
    API_CALLS = "api_calls"

    # Quality
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    AVERAGE_RESPONSE_LENGTH = "average_response_length"

    # Cost
    COST_USD = "cost_usd"
```

### Metrics Collector

```python
from craft.analytics import MetricsCollector, Timer

collector = MetricsCollector()

# Record metrics
collector.record(MetricType.RESPONSE_TIME, 250.5, tags={"provider": "anthropic"})

# Get aggregated statistics
stats = collector.get_stats(
    MetricType.RESPONSE_TIME,
    tags={"provider": "anthropic"},
    window_minutes=5
)

print(f"Average: {stats['avg']:.2f}ms")
print(f"Min: {stats['min']:.2f}ms")
print(f"Max: {stats['max']:.2f}ms")

# Get percentiles
p95 = collector.get_percentile(MetricType.RESPONSE_TIME, 95, window_minutes=5)
print(f"p95: {p95:.2f}ms")

# Timer context manager
with Timer(collector, MetricType.RESPONSE_TIME, tags={"operation": "chat"}):
    response = chatbot.chat("Hello")
```

### Time-Series Data

```python
# Get time-series metrics
timeseries = collector.get_timeseries(
    MetricType.RESPONSE_TIME,
    window_minutes=60,
    bucket_minutes=5
)

for bucket in timeseries:
    print(f"Time: {bucket['timestamp']}")
    print(f"  Avg: {bucket['avg']:.2f}ms")
    print(f"  Count: {bucket['count']}")
```

---

## Monitoring & Health Checks

### Overview

Monitor system health, components, and services.

**Features:**
- Component health checks
- System memory monitoring
- Async health checks with timeout
- Overall system status
- Health history

### Health Check System

```python
from craft.monitoring import HealthCheck, HealthStatus, ComponentHealth

# Create health check
health = HealthCheck()

# Add component checks
async def check_database():
    try:
        # Your check logic
        count = storage.count()
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message=f"Database operational ({count} records)",
            metadata={"count": count}
        )
    except Exception as e:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {str(e)}"
        )

health.add_check("database", check_database)

# Run checks
overall = await health.check_all()
print(f"System status: {overall.status.value}")

# Check individual component
db_health = await health.check_component("database")
print(f"Database status: {db_health.status.value}")

# Check if healthy
if health.is_healthy():
    print("All systems operational")
```

### Health Status Levels

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"      # All systems operational
    DEGRADED = "degraded"    # Functioning but with issues
    UNHEALTHY = "unhealthy"  # Critical issues
    UNKNOWN = "unknown"      # Unable to determine
```

### Pre-defined Health Checks

```python
from craft.monitoring.health import (
    check_storage_health,
    check_provider_health,
    check_memory_health,
)

# Add pre-defined checks
health.add_check("storage", lambda: check_storage_health(storage))
health.add_check("provider", lambda: check_provider_health(provider))
health.add_check("memory", check_memory_health)
```

---

## Advanced Logging

### Overview

Structured logging with JSON output and context support.

**Features:**
- Structured logging
- JSON output
- Context management
- File and console output
- Multiple log levels

### Basic Usage

```python
from craft.monitoring import AdvancedLogger, LogLevel

# Create logger
logger = AdvancedLogger("my-app", level=LogLevel.INFO)

# Log messages
logger.info("Application started")
logger.info("User logged in", user_id="123", action="login")
logger.warning("High memory usage", percent=85)
logger.error("Connection failed", service="database", retry=3)

# With context
request_logger = logger.with_context(request_id="req-456", user="alice")
request_logger.info("Processing request")
request_logger.info("Request completed", duration_ms=250)
```

### JSON Logging

```python
# JSON structured logs
logger = AdvancedLogger("my-app", json_logs=True)

logger.info("Event occurred", event_type="user_signup", user_id="123")

# Output (JSON):
# {
#   "timestamp": "2024-01-20T14:30:00",
#   "level": "INFO",
#   "message": "Event occurred",
#   "logger": "my-app",
#   "event_type": "user_signup",
#   "user_id": "123"
# }
```

### File Logging

```python
logger = AdvancedLogger(
    "my-app",
    level=LogLevel.INFO,
    json_logs=True,
    log_file="./logs/app.log"
)
```

---

## Alerting System

### Overview

Alert management for critical events and conditions.

**Features:**
- Multiple alert levels
- Alert handlers (email, logs, console)
- Alert history
- Alert resolution tracking
- Alert statistics

### Basic Usage

```python
from craft.monitoring import AlertManager, AlertLevel, console_alert_handler

# Create alert manager
alerts = AlertManager()

# Add handlers
alerts.add_handler(AlertLevel.WARNING, console_alert_handler)

# Trigger alerts
alerts.alert(
    AlertLevel.CRITICAL,
    "Database Down",
    "Unable to connect to database",
    source="database",
    metadata={"last_success": "2024-01-20 14:30:00"}
)

# Get active alerts
active = alerts.get_active_alerts()
for alert in active:
    print(f"[{alert.level.value}] {alert.title}: {alert.message}")

# Resolve alert
alerts.resolve(alert.id)
```

### Alert Levels

```python
class AlertLevel(Enum):
    INFO = "info"           # Informational
    WARNING = "warning"     # Requires attention
    ERROR = "error"         # Serious issue
    CRITICAL = "critical"   # System-critical
```

### Custom Alert Handlers

```python
def send_email_alert(alert):
    """Custom email alert handler."""
    if alert.level == AlertLevel.CRITICAL:
        # Send email
        send_email(
            to="admin@example.com",
            subject=f"[CRITICAL] {alert.title}",
            body=alert.message
        )

alerts.add_handler(AlertLevel.CRITICAL, send_email_alert)
```

### Alert Statistics

```python
stats = alerts.get_alert_stats(hours=24)
print(f"Total alerts: {stats['total_alerts']}")
print(f"By level: {stats['by_level']}")
print(f"By source: {stats['by_source']}")
print(f"Active: {stats['active']}")
print(f"Resolved: {stats['resolved']}")
```

---

## Production Example

Complete production setup with all features:

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.storage import PostgreSQLStorage
from craft.core.memory import Memory
from craft.i18n import Translator, detect_language
from craft.analytics import AnalyticsTracker, MetricsCollector, Timer
from craft.monitoring import (
    HealthCheck,
    AdvancedLogger,
    AlertManager,
    AlertLevel,
    console_alert_handler,
)

class ProductionChatbot:
    def __init__(self, api_key: str):
        # Logging
        self.logger = AdvancedLogger("production", level=LogLevel.INFO)

        # Storage
        storage = PostgreSQLStorage(host="localhost", database="craft")
        memory = Memory(storage=storage)

        # Provider & Chatbot
        provider = AnthropicProvider(api_key=api_key)
        self.chatbot = Chatbot(provider=provider, memory=memory)

        # Analytics
        self.analytics = AnalyticsTracker()
        self.metrics = MetricsCollector()

        # Health checks
        self.health = HealthCheck()
        # ... add checks

        # Alerts
        self.alerts = AlertManager()
        self.alerts.add_handler(AlertLevel.ERROR, console_alert_handler)

    async def chat(self, message: str, user_id: str = None):
        # Detect language
        lang = detect_language(message)
        translator = Translator(language=lang)

        # Track event
        self.analytics.track_event(
            EventType.MESSAGE_SENT,
            data={"message": message, "language": lang.value},
            user_id=user_id
        )

        # Process with timing
        with Timer(self.metrics, MetricType.RESPONSE_TIME):
            response = self.chatbot.chat(message)

        # Log
        self.logger.info("Chat completed", language=lang.value, user_id=user_id)

        return response.content
```

## Best Practices

### 1. Analytics

- Track key events (conversations, errors)
- Monitor response times and quality
- Export data regularly for analysis
- Set up dashboards for visualization

### 2. Monitoring

- Health check all critical components
- Set appropriate timeouts
- Check health before/after deployments
- Monitor resource usage (memory, CPU)

### 3. Alerting

- Set alert thresholds appropriately
- Don't alert on everything (alert fatigue)
- Critical alerts → immediate action
- Warning alerts → review regularly

### 4. Logging

- Use structured JSON logs in production
- Include context (request_id, user_id)
- Log errors with full stack traces
- Rotate log files to prevent disk space issues

### 5. Multi-language

- Auto-detect language when possible
- Provide language selection option
- Test with native speakers
- Keep translations up-to-date

## Examples

See the `examples/` directory:

- `i18n_multilanguage.py` - Multi-language support
- `analytics_metrics.py` - Analytics and metrics
- `monitoring_health.py` - Monitoring and health checks
- `phase6_complete.py` - Complete production example

## Learn More

- [Main Documentation](../README.md)
- [Storage Guide](STORAGE.md)
- [API Integration](API_INTEGRATION.md)
- [MCP Integration](MCP_INTEGRATION.md)
