# CRAFT Technical Stack

## Core Technologies

**Language**: Python 3.9+

**Build System**: setuptools with pyproject.toml

**Key Dependencies**:
- pydantic (data validation and models)
- httpx (async HTTP client)
- pyyaml (configuration)
- python-dotenv (environment variables)
- tenacity (retry logic)

## Optional Dependencies

**LLM Providers**: anthropic, openai, google-generativeai, boto3 (AWS), cohere

**RAG**: chromadb, sentence-transformers, faiss-cpu, pinecone-client, rank-bm25, flashrank

**Storage**: sqlalchemy, redis, pymongo

**API**: fastapi, uvicorn, websockets

**Observability**: langfuse, prometheus-client, opentelemetry, sentry-sdk

**Document Loaders**: pypdf, pandas, beautifulsoup4

**Testing**: pytest, pytest-asyncio, pytest-cov

**Code Quality**: black, ruff, mypy

## Frontend

**React Package** (`craft-react`):
- TypeScript
- React 18+
- Vite (build tool)
- ESLint + Prettier

## Common Commands

### Installation
```bash
# Basic install
pip install craft-chatbot

# With specific features
pip install 'craft-chatbot[anthropic]'
pip install 'craft-chatbot[rag]'
pip install 'craft-chatbot[all]'

# Development install
pip install -e ".[all]"
```

### Testing
```bash
# Run all tests
pytest

# With coverage
pytest --cov=craft --cov-report=html

# Specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Code Quality
```bash
# Format code
black craft/ tests/

# Lint
ruff check craft/ tests/

# Type check
mypy craft/
```

### Docker
```bash
# Start services
docker-compose up

# Build and run
docker-compose up --build
```

### React Package
```bash
cd craft-react

# Development
npm run dev

# Build
npm run build

# Type check
npm run typecheck

# Lint
npm run lint
```

## Configuration

Environment variables or YAML/JSON config files:
- Provider API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`
- CRAFT settings: `CRAFT_PROVIDER`, `CRAFT_LOG_LEVEL`, `CRAFT_STREAMING`
- Config file: `config.yaml` with provider, model, temperature, etc.
