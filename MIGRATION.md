# Migration Guide: CRAFT v1.x to v2.0

CRAFT v2.0 introduces significant architectural improvements to make agents more robust, observable, and capable. This guide helps you migrate your existing v1.x code to v2.0.

## 🚨 Breaking Changes

### 1. Provider System Refactor
The `Provider` class has been completely overhauled to support unified retry logic, streaming, and better error handling.

**v1.x:**
```python
from craft.providers import OpenAIProvider

provider = OpenAIProvider(api_key="...")
response = provider.chat(messages)
```

**v2.0:**
```python
from craft.providers import OpenAIProvider
from craft.core.typing import Message, Role

# Providers now strictly require Message objects
provider = OpenAIProvider(api_key="...")
messages = [Message(role=Role.USER, content="Hello")]
response = provider.chat(messages)
```

### 2. Tool Definition
The `@tool` decorator and `Tool` class have been enhanced for better validation and schema generation.

**v1.x:**
```python
def my_tool(arg1):
    """Description."""
    return "result"
```

**v2.0:**
```python
from craft.tools import tool

@tool
def my_tool(arg1: str) -> str:
    """
    Description.
    
    Args:
        arg1: Description of arg1
    """
    return "result"
```
*Note: Type hints and docstrings are now **mandatory** for tools to be registered correctly.*

### 3. Agent Initialization
The `Agent` class now takes specific parameters instead of a generic config object in some contexts, or uses a structured `AgentConfig`.

**v1.x:**
```python
agent = Agent(name="Bot", config={...})
```

**v2.0:**
```python
from craft.agents import Agent

agent = Agent(
    name="Bot",
    provider=provider,
    role="Assistant",
    goal="Help user",
    max_steps=10
)
```

## 🌟 New Features

### 1. Advanced RAG
New modules for Hybrid Search, Reranking, and Query Rewriting.
```python
from craft.rag import HybridRetriever

retriever = HybridRetriever(...)
docs = retriever.search("query")
```

### 2. Observability (Tracing)
Built-in tracing for debugging agent steps.
```bash
export CRAFT_TRACE_CLIENT_IO=2  # Enable detailed tracing output
```

### 3. Multi-Agent Consensus
New `Council` and `Debate` strategies for multi-agent collaboration.
```python
from craft.consensus import Council, DebateStrategy

council = Council(agents=[agent1, agent2], strategy=DebateStrategy())
result = council.decide("Should we deploy?")
```

### 4. Robust Error Handling
Agents now gracefully handle errors and retries.
```python
from craft.core.errors import AgentExecutionError

try:
    agent.run("task")
except AgentExecutionError as e:
    print(f"Failed with suggestion: {e.recovery_suggestion}")
```

## Migration Checklist

- [ ] Update all `Provider` instantiations.
- [ ] Convert all raw dictionaries in `chat()` calls to `Message` objects.
- [ ] Add type hints and Google-style docstrings to all custom tools.
- [ ] Decorate all tools with `@tool`.
- [ ] Update `Agent` initialization to use new signature.
- [ ] Replace custom RAG implementations with `craft.rag` components.
