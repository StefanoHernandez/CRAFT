# CRAFT Project Structure

## Repository Layout

```
craft/                      # Main Python package
├── core/                   # Core chatbot functionality
│   ├── chatbot.py         # Main Chatbot class (orchestrates everything)
│   ├── conversation.py    # Conversation management
│   ├── context.py         # Context handling
│   ├── memory.py          # Memory system
│   └── tool_calling.py    # MCP tool integration
├── providers/             # LLM provider implementations
│   ├── base.py           # Abstract Provider class, Message/Response models
│   ├── anthropic.py      # Anthropic Claude
│   ├── openai.py         # OpenAI GPT
│   ├── google.py         # Google Gemini
│   ├── azure_openai.py   # Azure OpenAI
│   ├── aws_bedrock.py    # AWS Bedrock
│   └── cohere.py         # Cohere
├── rag/                   # RAG system
│   ├── retrieval.py      # RetrievalEngine
│   ├── chunking.py       # Document chunking strategies
│   ├── advanced.py       # Hybrid search, reranking, query rewriting
│   ├── embeddings/       # Embedding providers
│   └── vectorstores/     # Vector store adapters
├── storage/               # Persistent storage adapters
│   ├── base.py           # Abstract StorageAdapter class
│   ├── sqlite.py         # SQLite implementation
│   ├── postgresql.py     # PostgreSQL implementation
│   ├── redis.py          # Redis implementation
│   └── mongodb.py        # MongoDB implementation
├── loaders/               # Document loaders
│   ├── base.py           # Base loader interface
│   ├── pdf.py            # PDF loader
│   ├── csv_loader.py     # CSV loader
│   └── web.py            # Web scraping loader
├── integrations/          # External integrations
│   ├── api/              # FastAPI server
│   │   ├── server.py     # Main API server
│   │   ├── auth.py       # API key authentication
│   │   └── rate_limiter.py
│   ├── widgets/          # Web widgets
│   ├── langfuse.py       # Langfuse observability
│   ├── prometheus.py     # Prometheus metrics
│   ├── opentelemetry.py  # OpenTelemetry tracing
│   └── sentry.py         # Sentry error tracking
├── mcp/                   # Model Context Protocol
│   ├── server.py         # MCP server implementation
│   ├── client.py         # MCP client
│   └── registry.py       # Tool registry
├── analytics/             # Analytics and metrics
├── monitoring/            # Health checks and logging
├── i18n/                  # Internationalization
└── utils/                 # Utilities (config, logging)

craft-react/               # React component package
├── src/
│   ├── CraftChat.tsx     # Main chat component
│   ├── components/       # UI components
│   ├── hooks/            # React hooks (useCraft)
│   └── types.ts          # TypeScript types
└── examples/             # React examples

examples/                  # Python usage examples
tests/                     # Test suite
├── unit/                 # Unit tests
└── conftest.py           # Pytest fixtures

docs/                      # Documentation
```

## Architecture Patterns

### Provider Pattern
All LLM providers inherit from `craft.providers.base.Provider` abstract class. Providers must implement:
- `chat()` - synchronous chat
- `achat()` - async chat
- `_validate_config()` - config validation

### Storage Adapter Pattern
All storage backends inherit from `craft.storage.base.StorageAdapter`. Required methods:
- `save()`, `load()`, `delete()`
- `list_conversations()`, `search()`
- `count()`, `clear()`

### Chatbot Orchestration
`craft.core.chatbot.Chatbot` is the main entry point that orchestrates:
- Provider communication
- Conversation management
- Memory persistence
- RAG retrieval
- Context injection

### Configuration
- Pydantic models for validation (BaseModel)
- YAML/JSON config files via `craft.utils.config`
- Environment variables via python-dotenv
- Provider-specific configs extend `ProviderConfig`

### Error Handling
- Tenacity for retry logic on provider calls
- Graceful degradation (RAG optional, memory optional)
- Detailed logging via `craft.utils.logging`

## Code Conventions

- **Type hints**: Use throughout (Python 3.9+ syntax)
- **Async support**: Provide both sync and async methods (`chat` / `achat`)
- **Docstrings**: Google-style docstrings for all public APIs
- **Formatting**: Black (line length 100)
- **Linting**: Ruff
- **Testing**: pytest with >80% coverage target
- **Imports**: Absolute imports from `craft.*`
- **Models**: Pydantic BaseModel for data structures
- **Enums**: Use for fixed choices (e.g., `Role`, `ChunkingStrategy`)

## Entry Points

- `craft.Chatbot` - Main chatbot class
- `craft.providers.*` - Provider implementations
- `craft.rag.RetrievalEngine` - RAG system
- `craft.storage.*` - Storage adapters
- `craft.integrations.api.CRAFTServer` - API server
- `craft.mcp.CRAFTMCPServer` - MCP server

## Testing Structure

- Unit tests in `tests/unit/` - test individual components
- Integration tests - test provider/storage integrations
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Fixtures in `tests/conftest.py`
- Mock external APIs in unit tests
