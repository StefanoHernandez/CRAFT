# 🚀 CRAFT - Chatbot & RAG Framework Toolkit

**CRAFT** is a flexible, provider-agnostic framework for building intelligent chatbots with RAG (Retrieval-Augmented Generation) capabilities. Switch between Anthropic, OpenAI, Google, and other LLM providers with just one line of code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🔌 **Provider-Agnostic**: Easily switch between Anthropic Claude, OpenAI GPT, Google Gemini, and more
- 🧠 **RAG Integration**: Built-in support for vector stores and retrieval systems (coming soon)
- ⚡ **Streaming Support**: Real-time streaming responses from all providers
- 💾 **Conversation Memory**: Persistent conversation storage with multiple backends
- 🌐 **Easy Integration**: REST API, WebSocket, and web widgets for instant deployment
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

### Phase 2 - RAG System 🚧
- [ ] Vector store adapters (ChromaDB, Pinecone, FAISS, Qdrant)
- [ ] Embedding providers
- [ ] Document chunking strategies
- [ ] Retrieval engine
- [ ] Context injection

### Phase 3 - Storage & Persistence 🚧
- [ ] SQLite adapter
- [ ] PostgreSQL adapter
- [ ] Redis adapter
- [ ] MongoDB adapter
- [ ] Conversation export/import

### Phase 4 - API & Integrations 📋
- [ ] FastAPI server
- [ ] WebSocket support
- [ ] REST API endpoints
- [ ] Authentication & rate limiting
- [ ] Vanilla JS widget
- [ ] React component

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
