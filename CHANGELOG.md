# Changelog

All notable changes to CRAFT will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-11-18

### Added - Production Observability Integrations
- **Langfuse Integration**
  - LLM-specific observability and tracing
  - Automatic trace generation for all chat interactions
  - Token usage tracking and cost analysis
  - RAG query tracing with retrieval analytics
  - Session tracking across multiple interactions
  - Custom metadata and tags support
  - User feedback integration

- **Prometheus Integration**
  - Metrics exporter for monitoring
  - Request counters by provider, model, and status
  - Response time histograms with percentiles
  - Token usage tracking (input/output)
  - Error rate monitoring
  - Custom labels and namespaces
  - HTTP server for Prometheus scraping

- **OpenTelemetry Integration**
  - Distributed tracing across services
  - Support for OTLP, Jaeger, and Zipkin exporters
  - Automatic span generation for chat operations
  - Custom spans and nested operations
  - Exception recording with stack traces
  - Resource attributes and metadata
  - Context propagation

- **Sentry Integration**
  - Error tracking and performance monitoring
  - Automatic exception capture with context
  - Performance transaction tracking
  - User context and identification
  - Custom tags and metadata
  - Release tracking and breadcrumbs
  - Performance profiling with sampling

- **React Component (@craft-ai/react v1.0.0)**
  - Complete TypeScript React component library
  - useCraft custom hook for state management
  - CraftChat main component with full UI
  - Streaming support with real-time updates
  - Theming system (light/dark/auto)
  - Markdown rendering support
  - Error handling and loading states
  - Responsive design
  - TypeScript definitions included
  - ESM and CJS builds

- **Examples**
  - integrations_langfuse.py: Langfuse tracing examples
  - integrations_prometheus.py: Prometheus metrics and Grafana queries
  - integrations_otel.py: OpenTelemetry distributed tracing
  - integrations_sentry.py: Sentry error tracking and performance

- **Documentation**
  - INTEGRATIONS.md: Comprehensive integration guide
  - Setup instructions for each integration
  - Grafana/Prometheus query examples
  - Best practices and troubleshooting
  - Performance benchmarks
  - craft-react/README.md: React component documentation

### Changed
- Updated pyproject.toml with optional integration dependencies
- Updated README.md with Production Integrations section
- Enhanced installation options for integrations

### Performance
- All integrations support graceful degradation
- Combined overhead <5ms per request with proper sampling
- Async trace sending (Langfuse) for minimal impact
- Configurable sampling rates for production use

## [1.2.0] - 2025-01-18

### Added - Phase 6: Advanced Features
- **Multi-language Support (i18n)**
  - Translator system with 10 languages (EN, IT, ES, FR, DE, PT, ZH, JA, KO, RU)
  - Auto-detect language from user input
  - Built-in translations for system messages
  - Language-specific prompt generation

- **Analytics & Metrics**
  - AnalyticsTracker for event tracking
  - MetricsCollector for aggregated metrics
  - Event types: conversation, provider, RAG, storage, API, system
  - Metric types: performance, usage, quality, cost
  - Real-time statistics and time-series data
  - Timer context manager for operation timing
  - Export/import analytics data
  - Percentile calculations (p50, p95, p99)

- **Monitoring & Health Checks**
  - HealthCheck system for component monitoring
  - Async health checks with timeout
  - Health status levels: healthy, degraded, unhealthy, unknown
  - Pre-defined health check functions
  - System memory monitoring support

- **Advanced Logging**
  - AdvancedLogger with structured logging
  - JSON output support
  - Context management (request_id, user_id, etc.)
  - File and console output
  - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

- **Alerting System**
  - AlertManager for critical events
  - Alert levels: INFO, WARNING, ERROR, CRITICAL
  - Alert handlers (console, logs, custom)
  - Alert resolution tracking
  - Alert history and statistics

- **Examples**
  - i18n_multilanguage.py: Multi-language chatbot demo
  - analytics_metrics.py: Analytics and metrics tracking
  - monitoring_health.py: Health checks and alerting
  - phase6_complete.py: Complete production example

- **Documentation**
  - ADVANCED_FEATURES.md: Comprehensive Phase 6 guide

## [1.1.0] - 2025-01-18

### Added - Phase 3: Storage & Persistence
- **Storage Adapters**
  - SQLiteStorage: File-based storage with JSON columns and FTS
  - PostgreSQLStorage: Production database with JSONB and GIN indexes
  - RedisStorage: In-memory cache with TTL and sorted set indexing
  - MongoDBStorage: NoSQL with text search indexes

- **Memory System**
  - Updated Memory class to support storage adapters
  - Optional persistent storage via storage parameter
  - Message trimming with max_messages limit
  - Search functionality across all backends

- **Migration Tools**
  - Storage migration utilities
  - Batch migration support with statistics
  - Export/import functionality

- **Examples**
  - storage_sqlite.py: Basic SQLite usage demo
  - storage_comparison.py: Performance comparison of all backends
  - storage_migration.py: Migration tool between storage backends

- **Documentation**
  - STORAGE.md: Comprehensive storage guide

## [1.0.0] - 2025-01-17

### Added - Phase 5: MCP Integration
- **MCP Server**
  - CRAFTMCPServer exposing CRAFT as MCP tools
  - Tools: craft_chat, craft_clear_conversation, craft_add_documents, craft_query_knowledge

- **MCP Client**
  - MCPToolClient for consuming external tools
  - ToolRegistry for managing both MCP and custom Python tools
  - ToolCallingMixin for adding tool capabilities to Chatbot

- **Examples**
  - mcp_server_example.py: MCP server usage
  - mcp_custom_tools.py: Custom tool integration

- **Documentation**
  - MCP_INTEGRATION.md: Comprehensive MCP integration guide

## [0.3.0] - 2025-01-16

### Added - Phase 4: API & Web Integration
- **FastAPI Server**
  - CRAFTServer with auto-generated docs
  - REST endpoints: /health, /chat, /chat/stream, /ws, /conversation/{id}
  - WebSocket support for real-time chat
  - Server-Sent Events for streaming

- **Security**
  - APIKeyManager with Bearer token authentication
  - Rate limiting middleware
  - CORS support

- **Web Widget**
  - Vanilla JavaScript widget (zero dependencies)
  - Light/Dark themes
  - Real-time streaming support
  - Responsive design

- **Examples**
  - api_server.py: Basic API server
  - api_client.py: Python client
  - api_with_rag.py: API server with RAG
  - widget_demo.html: Web widget demo

## [0.2.0] - 2025-01-15

### Added - Phase 2: RAG System
- **Embeddings**
  - Base embedding interface
  - OpenAIEmbedding provider
  - SentenceTransformerEmbedding (local)

- **Vector Stores**
  - ChromaVectorStore adapter
  - FAISSVectorStore adapter
  - PineconeVectorStore adapter

- **Document Processing**
  - DocumentChunker with 4 strategies: fixed-size, sentence, paragraph, semantic
  - RetrievalEngine orchestrating embeddings and vector search
  - Automatic context injection in Chatbot

- **Examples**
  - rag_basic.py: Basic RAG usage
  - rag_advanced.py: Advanced RAG configuration
  - rag_document_qa.py: Document Q&A system

## [0.1.0] - 2025-01-14

### Added - Phase 1: Core Framework
- **Providers**
  - Base provider interface
  - AnthropicProvider with streaming
  - OpenAIProvider with streaming
  - GoogleProvider with streaming

- **Core Components**
  - Chatbot class with conversation management
  - Conversation and Message models
  - Context management
  - Memory system (in-memory)

- **Configuration**
  - YAML/JSON/environment variable support
  - ConfigLoader utility

- **Utilities**
  - Colored logging system
  - Docker Compose setup

- **Examples**
  - basic_chat.py: Simple chatbot
  - streaming_chat.py: Streaming responses
  - multi_provider.py: Provider comparison
  - config_example.py: Configuration demo

## [Unreleased]

### Planned
- A/B testing framework
- Prompt optimization tools
- Fine-tuning helpers
- Advanced RAG features (hybrid search, reranking)
- Performance optimizations
- Enhanced security features
- Additional LLM provider integrations

---

## Version History

- **1.3.0** - Production Observability (Langfuse, Prometheus, OpenTelemetry, Sentry) + React Component
- **1.2.0** - Phase 6: Advanced Features (i18n, Analytics, Monitoring)
- **1.1.0** - Phase 3: Storage & Persistence
- **1.0.0** - Phase 5: MCP Integration (production ready)
- **0.3.0** - Phase 4: API & Web Integration
- **0.2.0** - Phase 2: RAG System
- **0.1.0** - Phase 1: Core Framework

[1.3.0]: https://github.com/StefanoHernandez/CRAFT/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/StefanoHernandez/CRAFT/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/StefanoHernandez/CRAFT/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/StefanoHernandez/CRAFT/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/StefanoHernandez/CRAFT/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/StefanoHernandez/CRAFT/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/StefanoHernandez/CRAFT/releases/tag/v0.1.0
