# 🚀 CRAFT - Chatbot & RAG Framework Toolkit

**CRAFT** is a flexible, provider-agnostic framework for building intelligent chatbots with RAG (Retrieval-Augmented Generation) capabilities. Switch between Anthropic, OpenAI, Google, and other LLM providers with just one line of code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🔌 **Provider-Agnostic**: Easily switch between Anthropic Claude, OpenAI GPT, Google Gemini, and more
- 🧠 **RAG Integration**: Complete RAG system with embeddings, vector stores, and retrieval ✅
- 📚 **Multiple Vector Stores**: ChromaDB, FAISS, Pinecone support with adapter pattern ✅
- 🎯 **Smart Document Chunking**: Fixed-size, sentence, paragraph, and semantic strategies ✅
- ⚡ **Streaming Support**: Real-time streaming responses from all providers
- 💾 **Conversation Memory**: Persistent conversation storage with multiple backends
- 🌐 **Easy Integration**: REST API, WebSocket, and web widgets for instant deployment ✅
- 🛠️ **MCP Support**: Extend with custom tools via Model Context Protocol (coming soon)
- 🎨 **Highly Configurable**: YAML/JSON config files or environment variables
- 🐳 **Docker Ready**: Full Docker Compose setup included

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

# All providers
pip install 'craft-chatbot[all-providers]'
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

### Basic Example

```python
from craft import Chatbot
from craft.providers import AnthropicProvider

# Create a chatbot in 3 lines
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-api-key"),
    system_prompt="You are a helpful assistant.",
    memory=True
)

# Chat!
response = chatbot.chat("What is CRAFT?")
print(response.content)
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
chatbot = Chatbot(provider=OpenAIProvider(model="gpt-4-turbo-preview"))

# Google Gemini
chatbot = Chatbot(provider=GoogleProvider(model="gemini-1.5-pro"))

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

---

## 📚 Examples

### 1. Basic Chat

```python
from craft import Chatbot
from craft.providers import AnthropicProvider

chatbot = Chatbot(
    provider=AnthropicProvider(model="claude-3-5-sonnet-20241022"),
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
  model: claude-3-5-sonnet-20241022
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
    AnthropicProvider(model="claude-3-5-sonnet-20241022"),
    OpenAIProvider(model="gpt-4-turbo-preview"),
    GoogleProvider(model="gemini-1.5-pro"),
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
        "model": "claude-3-5-sonnet-20241022",
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
    model="claude-3-5-sonnet-20241022",
    api_key="your-key",
    temperature=0.7,
    max_tokens=4096,
)
```

**Supported Models:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### OpenAI GPT

```python
from craft.providers import OpenAIProvider

provider = OpenAIProvider(
    model="gpt-4-turbo-preview",
    api_key="your-key",
    temperature=0.7,
)
```

**Supported Models:**
- `gpt-4-turbo-preview`
- `gpt-4`
- `gpt-3.5-turbo`

### Google Gemini

```python
from craft.providers import GoogleProvider

provider = GoogleProvider(
    model="gemini-1.5-pro",
    api_key="your-key",
    temperature=0.7,
)
```

**Supported Models:**
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-pro`

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

### Phase 3 - Storage & Persistence 🚧
- [ ] SQLite adapter
- [ ] PostgreSQL adapter
- [ ] Redis adapter
- [ ] MongoDB adapter
- [ ] Conversation export/import

### Phase 4 - API & Integrations ✅
- [x] FastAPI server with auto-generated docs
- [x] WebSocket support for real-time chat
- [x] REST API endpoints (chat, streaming, conversations)
- [x] Authentication & API key management
- [x] Rate limiting middleware
- [x] CORS support
- [x] Vanilla JS widget (no dependencies!)
- [ ] React component (coming soon)

### Phase 5 - MCP Integration 📋
- [ ] MCP server implementation
- [ ] MCP client for consuming tools
- [ ] Tool registry
- [ ] Custom tool templates

### Phase 6 - Advanced Features 📋
- [ ] Multi-language support
- [ ] Analytics & metrics
- [ ] A/B testing framework
- [ ] Prompt optimization
- [ ] Fine-tuning helpers

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
