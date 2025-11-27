# 🚀 CRAFT - Chatbot & RAG Framework Toolkit

**CRAFT** is a flexible, provider-agnostic framework for building intelligent chatbots with RAG (Retrieval-Augmented Generation) capabilities. Switch between Anthropic, OpenAI, Google, and other LLM providers with just one line of code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

### Core Framework
- 🤖 **Agent System**: Autonomous agents with roles, goals, and backstories (v2.0) ✅
- 🛠️ **Tool System**: Type-safe tools with auto-generated schemas (v2.0) ✅
- 🔌 **Provider-Agnostic**: Switch between 6+ LLM providers with one line of code ✅
  - Anthropic Claude, OpenAI GPT, Google Gemini
  - **NEW in v1.4**: Azure OpenAI, AWS Bedrock, Cohere ✅
- ⚡ **Streaming Support**: Real-time streaming responses from all providers
- 💾 **Persistent Storage**: SQLite, PostgreSQL, Redis, MongoDB adapters ✅
- 🎨 **Highly Configurable**: YAML/JSON config files or environment variables
- 🐳 **Docker Ready**: Full Docker Compose setup included
- 🎯 **TOON Format**: 30-60% fewer tokens than JSON for LLM communication ✅

### Advanced Capabilities
- 🤝 **Multi-Agent Collaboration**: Council and Debate strategies (v2.0) ✅
- 🧠 **Complete RAG System**: Embeddings, vector stores, and retrieval ✅
- 📚 **Multiple Vector Stores**: ChromaDB, FAISS, Pinecone support ✅
- 🔍 **Hybrid Search**: Dense + sparse retrieval with RRF (v1.4) ✅
- 🎯 **Reranking**: Cross-encoder models for better results (v1.4) ✅
- ✍️ **Query Rewriting**: Expansion, decomposition, HyDE (v1.4) ✅

### Production & Integration
- 🌐 **Easy Integration**: REST API, WebSocket, and React widget ✅
- 🛠️ **MCP Support**: Full Model Context Protocol integration ✅
- 🔍 **Observability**: Built-in tracing and OpenTelemetry support (v2.0) ✅
- 📊 **Enterprise Ready**: Azure OpenAI, AWS Bedrock support (v1.4) ✅

> [!IMPORTANT]
> **Migrating from v1.x?** Check out the [Migration Guide](./MIGRATION.md) for breaking changes and new features.

---

## 📦 Installation

### Basic Installation

```bash
pip install craft-chatbot
```

### With Specific Providers

```bash
# Anthropic Claude
pip install 'craft-chatbot[anthropic]'

# OpenAI GPT
pip install 'craft-chatbot[openai]'

# Google Gemini
pip install 'craft-chatbot[google]'

# Azure OpenAI (v1.4+)
pip install 'craft-chatbot[openai]'  # Uses same openai package

# AWS Bedrock (v1.4+)
pip install 'craft-chatbot[aws]'

# Cohere (v1.4+)
pip install 'craft-chatbot[cohere]'

# All providers
pip install 'craft-chatbot[all-providers]'
```

### With Additional Features

```bash
# RAG with vector stores
pip install 'craft-chatbot[rag]'

# Document loaders (PDF, CSV, Web) - v1.4+
pip install 'craft-chatbot[loaders]'

# Advanced RAG (hybrid search, reranking, query rewriting) - v1.4+
pip install 'craft-chatbot[advanced-rag]'

# Langfuse (LLM observability)
pip install 'craft-chatbot[langfuse]'

# Prometheus (metrics)
pip install 'craft-chatbot[prometheus]'

# OpenTelemetry (distributed tracing)
pip install 'craft-chatbot[opentelemetry]'

# Sentry (error tracking)
pip install 'craft-chatbot[sentry]'

# All integrations
pip install 'craft-chatbot[all-integrations]'
```

### Full Installation (All Features)

```bash
pip install 'craft-chatbot[all]'
```

### Development Installation

```bash
git clone https://github.com/StefanoHernandez/CRAFT.git
cd CRAFT
pip install -e ".[all]"
```

---

## 🚀 Quick Start

### Basic Agent Example
```python
from craft.agents import Agent
from craft.providers import AnthropicProvider
from craft.tools import tool

# 1. Define a tool
@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"Sunny in {location}"

# 2. Create an agent
agent = Agent(
    name="WeatherBot",
    role="Assistant",
    goal="Help users with weather info",
    provider=AnthropicProvider(api_key="..."),
    tools=[get_weather]
)

# 3. Run the agent
result = agent.run("What's the weather in London?")
print(result.text)
```

### Streaming Example

```python
# Enable streaming for real-time responses
for chunk in chatbot.chat("Explain quantum computing", stream=True):
    print(chunk.content, end="", flush=True)
```

### Switch Providers

```python
from craft.providers import OpenAIProvider, GoogleProvider

# OpenAI
chatbot = Chatbot(provider=OpenAIProvider(model="gpt-4o"))

# Google Gemini
chatbot = Chatbot(provider=GoogleProvider(model="gemini-2.5-pro"))

# That's it! Same API, different providers
```

### RAG (Retrieval-Augmented Generation)

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore

# Create RAG components
embeddings = SentenceTransformerEmbedding(model="all-MiniLM-L6-v2")
vector_store = ChromaVectorStore(collection_name="my_docs")
rag = RetrievalEngine(
    embedding_provider=embeddings,
    vector_store=vector_store
)

# Add documents to knowledge base
documents = [
    "CRAFT is a chatbot framework with RAG support.",
    "It supports multiple LLM providers and vector stores.",
]
rag.add_documents(documents)

# Create chatbot with RAG
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    rag=rag  # Enable RAG!
)

# Ask questions about your documents
response = chatbot.chat("What is CRAFT?")
# The chatbot will retrieve relevant context and use it to answer!
```

### API Server & Web Integration

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations.api import CRAFTServer

# Create chatbot
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    memory=True
)

# Create API server
server = CRAFTServer(chatbot=chatbot, enable_cors=True)

# Run server
server.run(host="0.0.0.0", port=8000)
# API Docs: http://localhost:8000/docs
# WebSocket: ws://localhost:8000/ws
```

**Integrate into any website** (JavaScript Widget):

```html
<!-- Add to your HTML -->
<script src="craft-widget.js"></script>
<script>
  CRAFT.init({
    apiUrl: 'https://your-api-server.com',
    theme: 'light',
    position: 'bottom-right'
  });
</script>
```

That's it! The chat widget appears on your site 🎉

### Storage & Persistence

**Persist conversations** with multiple storage backends:

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.storage import PostgreSQLStorage

# Create storage backend
storage = PostgreSQLStorage(
    host="localhost",
    database="craft",
    username="postgres",
    password="your-password"
)

# Create chatbot with persistent memory
from craft.core.memory import Memory
memory = Memory(storage=storage, max_messages=100)

chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    memory=memory
)

# Conversations are automatically saved!
chatbot.chat("Hello!")

# Load conversation later
conversation = storage.load(chatbot.conversation.id)
```

**Available Storage Backends:**
- **SQLiteStorage**: File-based, perfect for development
- **PostgreSQLStorage**: Production-ready with full-text search
- **RedisStorage**: In-memory cache with TTL support
- **MongoDBStorage**: NoSQL with flexible schemas

```python
from craft.storage import SQLiteStorage, RedisStorage, MongoDBStorage

# SQLite (development)
storage = SQLiteStorage(database_path="./conversations.db")

# Redis (caching/sessions)
storage = RedisStorage(host="localhost", ttl=3600)

# MongoDB (scalability)
storage = MongoDBStorage(host="localhost", database="craft")
```

**Migrate between storage backends:**

```python
from examples.storage_migration import migrate_storage

# Migrate from SQLite to PostgreSQL
migrate_storage(
    source=SQLiteStorage("./dev.db"),
    destination=PostgreSQLStorage(...),
    batch_size=100
)
```

### Advanced Features (Phase 6)

**Multi-language Support:**

```python
from craft.i18n import Translator, Language, detect_language

# Auto-detect language
user_message = "Ciao! Come stai?"
lang = detect_language(user_message)  # Language.ITALIAN

# Create translator
translator = Translator(language=lang)
print(translator.get("welcome"))  # "Benvenuto in CRAFT"

# Chatbot with language instruction
lang_prompt = translator.translate_prompt("You are a helpful assistant.")
chatbot = Chatbot(provider=provider, system_prompt=lang_prompt)
```

**Analytics & Metrics:**

```python
from craft.analytics import AnalyticsTracker, EventType, MetricType, Timer

# Track events
tracker = AnalyticsTracker()
tracker.track_event(EventType.MESSAGE_SENT, data={"message": "Hello"})

# Track metrics
tracker.track_metric(MetricType.RESPONSE_TIME, value=250.5)

# Get statistics
stats = tracker.get_statistics(hours=24)
print(f"Total events: {stats['total_events']}")
```

**Monitoring & Health Checks:**

```python
from craft.monitoring import HealthCheck, AdvancedLogger, AlertManager

# Health checks
health = HealthCheck()
health.add_check("database", check_database)
status = await health.check_all()

# Advanced logging
logger = AdvancedLogger("my-app", json_logs=True)
logger.info("Event occurred", user_id="123")

# Alerting
alerts = AlertManager()
alerts.alert(AlertLevel.CRITICAL, "Service Down", "Database unreachable")
```

### MCP Integration

**Expose CRAFT as an MCP Server:**

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.mcp import CRAFTMCPServer

chatbot = Chatbot(provider=AnthropicProvider(api_key="your-key"))
server = CRAFTMCPServer(chatbot=chatbot)
await server.run()  # Exposes chat, RAG, and conversation tools
```

**Use External MCP Tools:**

```python
from craft.core.tool_calling import ToolCallingMixin

class ToolEnabledChatbot(Chatbot, ToolCallingMixin):
    def __init__(self, *args, **kwargs):
        Chatbot.__init__(self, *args, **kwargs)
        ToolCallingMixin.__init__(self)

chatbot = ToolEnabledChatbot(provider=AnthropicProvider(api_key="your-key"))

# Connect to external MCP server
await chatbot.add_mcp_server("path/to/server.py")

# Execute tools
result = await chatbot.execute_tool("tool_name", {"arg": "value"})
```

**Add Custom Tools:**

```python
def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72°F"

chatbot.add_custom_tool(
    name="get_weather",
    func=get_weather,
    description="Get current weather",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
)
```

---

## 📚 Examples

### 1. Basic Chat

```python
from craft import Chatbot
from craft.providers import AnthropicProvider

chatbot = Chatbot(
    provider=AnthropicProvider(model="claude-sonnet-4.5"),
    memory=True
)

# Simple conversation
response = chatbot.chat("Hello!")
print(response.content)

# Conversation history is automatically maintained
response = chatbot.chat("What did I just say?")
print(response.content)  # Will reference your "Hello!"
```

### 2. Configuration File

**config.yaml:**
```yaml
provider: anthropic
provider_config:
  model: claude-sonnet-4.5
  temperature: 0.7

streaming: true
memory_enabled: true
log_level: INFO
```

**Python:**
```python
from craft.utils.config import load_config
from craft import Chatbot

config = load_config("config.yaml")
# Chatbot automatically configured from file
```

### 3. Multi-Provider Comparison

```python
from craft import Chatbot
from craft.providers import AnthropicProvider, OpenAIProvider, GoogleProvider

providers = [
    AnthropicProvider(model="claude-sonnet-4.5"),
    OpenAIProvider(model="gpt-4o"),
    GoogleProvider(model="gemini-2.5-pro"),
]

question = "What is the future of AI?"

for provider in providers:
    chatbot = Chatbot(provider=provider)
    response = chatbot.chat(question)
    print(f"\n{provider.name}: {response.content}")
```

### 4. RAG with Document Q&A

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine, RetrievalConfig, ChunkConfig, ChunkingStrategy
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore

# Configure chunking and retrieval
chunk_config = ChunkConfig(
    strategy=ChunkingStrategy.SENTENCE,
    chunk_size=512,
    chunk_overlap=50
)

retrieval_config = RetrievalConfig(
    top_k=3,  # Retrieve top 3 chunks
    score_threshold=0.5,
    chunk_config=chunk_config
)

# Setup RAG
embeddings = SentenceTransformerEmbedding()
vector_store = ChromaVectorStore(collection_name="docs")
rag = RetrievalEngine(
    embedding_provider=embeddings,
    vector_store=vector_store,
    config=retrieval_config
)

# Load your documents
with open("documentation.txt", "r") as f:
    docs = [f.read()]

rag.add_documents(docs, metadatas=[{"source": "docs"}], chunk=True)

# Create RAG chatbot
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    rag=rag,
    system_prompt="Answer based on the provided documentation."
)

# Ask questions about your documents
response = chatbot.chat("How do I configure the system?")
print(response.content)
```

### 5. API Server with RAG

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore
from craft.integrations.api import CRAFTServer

# Setup RAG
embeddings = SentenceTransformerEmbedding()
vector_store = ChromaVectorStore(collection_name="docs")
rag = RetrievalEngine(embeddings, vector_store)
rag.add_documents(["CRAFT is awesome!", "It has an API!"])

# Create chatbot
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    rag=rag,
    memory=True
)

# Create and run server
server = CRAFTServer(chatbot=chatbot)
server.run(port=8000)

# Now you have:
# - REST API: http://localhost:8000/chat
# - WebSocket: ws://localhost:8000/ws
# - API Docs: http://localhost:8000/docs
```

---

## 🌐 API & Web Integration

### REST API

CRAFT includes a full-featured FastAPI server:

```python
from craft.integrations.api import CRAFTServer
from craft.integrations.api.auth import APIKeyManager
from craft.integrations.api.rate_limiter import RateLimiter

# Optional: Setup authentication
api_keys = APIKeyManager()
api_key = api_keys.create_key(name="client", rate_limit=100)

# Optional: Rate limiting
rate_limiter = RateLimiter(requests_per_minute=60)

# Create server
server = CRAFTServer(
    chatbot=chatbot,
    api_key_manager=api_keys,
    rate_limiter=rate_limiter,
    enable_cors=True
)

server.run(port=8000)
```

**API Endpoints:**
- `GET /health` - Health check
- `POST /chat` - Send message (non-streaming)
- `POST /chat/stream` - Send message (streaming SSE)
- `WebSocket /ws` - Real-time bidirectional chat
- `GET /conversation/{id}` - Get conversation details
- `DELETE /conversation/{id}` - Delete conversation

**Interactive docs** at: `http://localhost:8000/docs`

### JavaScript Widget

Add a chat widget to any website in 2 lines:

```html
<script src="craft-widget.js"></script>
<script>
  CRAFT.init({
    apiUrl: 'http://localhost:8000',
    apiKey: 'your-api-key',  // Optional
    theme: 'light',  // or 'dark'
    position: 'bottom-right',
    title: 'AI Assistant',
    enableStreaming: true,
    useRAG: true
  });
</script>
```

**Features:**
- 🎨 Light/Dark themes
- ⚡ Real-time streaming
- 📱 Responsive design
- 🔒 Secure (API key auth)
- 🚫 No dependencies
- 💬 Conversation history

### React Component

**React/TypeScript component with full TypeScript support:**

```bash
npm install @craft-ai/react
```

```tsx
import { CraftChat } from '@craft-ai/react'
import '@craft-ai/react/styles.css'

function App() {
  return (
    <CraftChat
      config={{
        apiUrl: 'http://localhost:8000',
        stream: true,
      }}
      theme="auto"  // 'light' | 'dark' | 'auto'
      welcomeMessage="👋 Hi! How can I help you today?"
      enableMarkdown={true}
      showTimestamp={false}
    />
  )
}
```

**Custom hook for building your own UI:**

```tsx
import { useCraft } from '@craft-ai/react'

function MyChat() {
  const { messages, isLoading, sendMessage } = useCraft({
    apiUrl: 'http://localhost:8000',
    stream: true,
  })

  return (
    <div>
      {messages.map(msg => <div key={msg.id}>{msg.content}</div>)}
      <button onClick={() => sendMessage('Hello!')}>Send</button>
    </div>
  )
}
```

**Features:**
- 🎣 Custom hooks (`useCraft`)
- 🎨 Theming (light/dark/auto)
- ⚡ Streaming support
- 📦 TypeScript definitions
- 🔧 Fully customizable
- 📱 Mobile responsive

[View React Docs →](./craft-react/README.md)

### Python API Client

```python
import requests

# Send message
response = requests.post('http://localhost:8000/chat', json={
    'message': 'Hello!',
    'use_rag': True
})

data = response.json()
print(data['content'])  # Assistant response
```

---

## 🔍 Production Integrations

**Monitor, trace, and debug your chatbot in production** with industry-standard observability tools.

### Langfuse - LLM Observability

```bash
pip install craft-chatbot[langfuse]
```

```python
from craft.integrations import LangfuseTracer

tracer = LangfuseTracer(public_key="pk-lf-...", secret_key="sk-lf-...")
chatbot = tracer.wrap_chatbot(chatbot)

# Automatic trace generation, token tracking, and cost analysis
# View traces at: https://cloud.langfuse.com
```

### Prometheus - Metrics & Monitoring

```bash
pip install craft-chatbot[prometheus]
```

```python
from craft.integrations import PrometheusExporter

exporter = PrometheusExporter(port=8000, namespace="craft")
chatbot = exporter.wrap_chatbot(chatbot)

# Metrics available at: http://localhost:8000/metrics
# Track: requests, response times, tokens, errors
```

### OpenTelemetry - Distributed Tracing

```bash
pip install craft-chatbot[opentelemetry]
```

```python
from craft.integrations import OpenTelemetryTracer

tracer = OpenTelemetryTracer(
    service_name="craft-chatbot",
    exporter_type="otlp",
    otlp_endpoint="http://jaeger:4317"
)
chatbot = tracer.wrap_chatbot(chatbot)

# Works with: Jaeger, Grafana Tempo, Honeycomb, etc.
```

### Sentry - Error Tracking

```bash
pip install craft-chatbot[sentry]
```

```python
from craft.integrations import SentryIntegration

sentry = SentryIntegration(
    dsn="https://...@sentry.io/...",
    environment="production",
    traces_sample_rate=0.1
)
chatbot = sentry.wrap_chatbot(chatbot)

# Automatic error capture and performance monitoring
```

### All Integrations Together

```python
# Combine multiple integrations for complete observability
langfuse = LangfuseTracer()
prometheus = PrometheusExporter(port=8000)
otel = OpenTelemetryTracer(service_name="craft")
sentry = SentryIntegration()

# Wrap chatbot with all integrations
chatbot = Chatbot(provider=AnthropicProvider())
chatbot = langfuse.wrap_chatbot(chatbot)
chatbot = prometheus.wrap_chatbot(chatbot)
chatbot = otel.wrap_chatbot(chatbot)
chatbot = sentry.wrap_chatbot(chatbot)

# Single call → full observability stack
response = chatbot.chat("Hello!")
```

**Benefits:**
- 📊 **Langfuse**: LLM-specific insights and cost tracking
- 📈 **Prometheus**: Real-time metrics and alerting
- 🔍 **OpenTelemetry**: Distributed tracing across services
- 🐛 **Sentry**: Error tracking and performance profiling

[View Integration Docs →](./INTEGRATIONS.md) | [Examples →](./examples/)

---

## 🐳 Docker Setup

### Quick Start with Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Start services
docker-compose up
```

### Docker Compose Services

- **craft**: Main CRAFT application
- **redis**: Optional caching/session storage
- **postgres**: Optional persistent conversation storage

---

## 🔧 Configuration

### Environment Variables

```bash
# Provider API Keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...

# CRAFT Settings
export CRAFT_PROVIDER=anthropic
export CRAFT_STREAMING=true
export CRAFT_LOG_LEVEL=INFO
```

### Programmatic Configuration

```python
from craft.utils.config import Config

config = Config(
    provider="anthropic",
    streaming=True,
    memory_enabled=True,
    log_level="DEBUG",
    provider_config={
        "model": "claude-sonnet-4.5",
        "temperature": 0.8,
        "max_tokens": 4096,
    }
)
```

---

## 📖 Provider Details

### Anthropic Claude

```python
from craft.providers import AnthropicProvider

provider = AnthropicProvider(
    model="claude-sonnet-4.5",
    api_key="your-key",
    temperature=0.7,
    max_tokens=4096,
)
```

**Supported Models:**
- `claude-sonnet-4.5` (recommended)
- `claude-opus-4.5-20240229`
- `claude-sonnet-4.5-20240229`
- `claude-haiku-4.5-20240307`

### OpenAI GPT

```python
from craft.providers import OpenAIProvider

provider = OpenAIProvider(
    model="gpt-4o",
    api_key="your-key",
    temperature=0.7,
)
```

**Supported Models:**
- `gpt-4o`
- `gpt-4o`
- `gpt-3.5-turbo`

### Google Gemini

```python
from craft.providers import GoogleProvider

provider = GoogleProvider(
    model="gemini-2.5-pro",
    api_key="your-key",
    temperature=0.7,
)
```

**Supported Models:**
- `gemini-2.5-pro`
- `gemini-2.5-flash`
- `gemini-pro`

---

## 🧪 Testing

CRAFT has comprehensive test coverage with unit and integration tests.

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=craft --cov-report=html

# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests
```

### Test Structure

```
tests/
├── unit/               # Unit tests
│   ├── test_chatbot.py
│   ├── test_conversation.py
│   ├── test_storage.py
│   ├── test_analytics.py
│   └── test_i18n.py
├── integration/        # Integration tests
└── conftest.py         # Shared fixtures
```

### Coverage

We maintain >80% test coverage. View the coverage report:

```bash
pytest --cov=craft --cov-report=html
open htmlcov/index.html
```

### Continuous Integration

All PRs must pass:
- ✅ Unit tests on Python 3.9, 3.10, 3.11, 3.12
- ✅ Integration tests with real databases
- ✅ Code linting (black, ruff)
- ✅ Type checking (mypy)

---

## 🛣️ Roadmap

### Phase 1 - Core Framework ✅
- [x] Provider interface (Anthropic, OpenAI, Google)
- [x] Streaming support
- [x] Conversation management
- [x] Memory system
- [x] Configuration system
- [x] Docker support

### Phase 2 - RAG System ✅
- [x] Vector store adapters (ChromaDB, FAISS, Pinecone)
- [x] Embedding providers (OpenAI, Sentence Transformers)
- [x] Document chunking strategies (fixed, sentence, paragraph)
- [x] Retrieval engine with scoring
- [x] Context injection in Chatbot

### Phase 3 - Storage & Persistence ✅
- [x] SQLite adapter
- [x] PostgreSQL adapter with JSONB and full-text search
- [x] Redis adapter with TTL support
- [x] MongoDB adapter with text search indexes
- [x] Conversation export/import functionality
- [x] Storage migration tools
- [x] Integration with Memory system

### Phase 4 - API & Integrations ✅
- [x] FastAPI server with auto-generated docs
- [x] WebSocket support for real-time chat
- [x] REST API endpoints (chat, streaming, conversations)
- [x] Authentication & API key management
- [x] Rate limiting middleware
- [x] CORS support
- [x] Vanilla JS widget (no dependencies!)
- [x] React component (@craft-ai/react) with TypeScript

### Phase 5 - MCP Integration ✅
- [x] MCP server implementation (expose CRAFT as tools)
- [x] MCP client for consuming external tools
- [x] Tool registry and management
- [x] Custom Python tool integration
- [x] Function calling support
- [x] Comprehensive MCP documentation

### Phase 6 - Advanced Features ✅
- [x] Multi-language support (i18n) - 10 languages
- [x] Analytics & metrics tracking
- [x] Advanced monitoring & logging
- [x] Health checks system
- [x] Alerting system
- [ ] A/B testing framework (future)
- [ ] Prompt optimization (future)
- [ ] Fine-tuning helpers (future)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by the need for a truly provider-agnostic chatbot framework
- Built with love for the AI community

---

## 📞 Support

- 📧 Issues: [GitHub Issues](https://github.com/StefanoHernandez/CRAFT/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/StefanoHernandez/CRAFT/discussions)

---

**Made with ❤️ by the CRAFT team**
