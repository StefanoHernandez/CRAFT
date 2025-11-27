# 🏛️ Council Consensus System - Documentation

## Overview

The **Council Consensus System** enables multi-agent deliberation where agents with different perspectives (and potentially different LLM providers) debate a topic and reach a consensus through structured discussion.

Inspired by:
- **Andrej Karpathy's "Council of LLMs"** concept
- **Machine Theory of Mind** research
- Democratic voting systems

---

## Key Features

✨ **Multi-Provider Support**: Each agent can use a different LLM provider  
🎯 **Debate Strategy**: Karpathy-style multi-round debate with chairman synthesis  
🌍 **Latest Models**: Gemini 2.0, Claude 3.5, GPT-4o, Mistral, Grok 4.1  
🔄 **Async Execution**: Non-blocking multi-agent communication  
📊 **Structured Output**: Debate transcripts, vote counts, rationale

---

## Quick Start

```python
import asyncio
from craft.agents.agent import Agent
from craft.providers import (
    GoogleProvider,      # Gemini
    AnthropicProvider,   # Claude
    OpenAIProvider,      # GPT
    MistralProvider,     # Mistral AI
    xAIProvider          # Grok
)
from craft.consensus.council import Council, CouncilConfig, ConsensusStrategy

# Chairman: Gemini 2.0 Flash (synthesis)
chairman = Agent(
    name="Chairman",
    provider=GoogleProvider(model="gemini-2.0-flash-exp"),
    role="Council Chairman"
)

# Members: Different providers!
strategist = Agent(
    name="Strategist",
    provider=AnthropicProvider(model="claude-sonnet-4.5"),
    role="Strategic Analyst"
)

innovator = Agent(
    name="Innovator",
    provider=OpenAIProvider(model="gpt-4o"),
    role="Innovation Lead"
)

expert = Agent(
    name="Expert",
    provider=MistralProvider(model="mistral-large-latest"),
    role="Technical Expert"
)

trendsetter = Agent(
    name="Trendsetter",
    provider=xAIProvider(model="grok-2-1212"),
    role="Trend Analyst"
)

# Create Council
council = Council(config=CouncilConfig(
    name="AI Elite Council",
    strategy=ConsensusStrategy.DEBATE,
    agents=[strategist, innovator, expert, trendsetter],
    chairman=chairman,
    max_rounds=3
))

# Deliberate
result = await council.deliberate(
    "Should we migrate to microservices architecture?"
)

print(result.decision)
print(f"Consensus: {result.consensus_reached}")
print(f"Rounds: {result.iterations}")
```

---

## Available Providers

### 🌐 OpenRouter (400+ Models)
```python
from craft.providers import OpenRouterProvider

provider = OpenRouterProvider(
    model="google/gemini-2.0-flash-exp:free"  # FREE!
)

# Other popular models:
# - anthropic/claude-3.5-sonnet
# - openai/gpt-4o
# - x-ai/grok-4.1
# - mistralai/mistral-large
# - meta-llama/llama-3.3-70b-instruct
```

### 🤖 xAI Grok
```python
from craft.providers import xAIProvider

provider = xAIProvider(model="grok-2-1212")
```

### 🇫🇷 Mistral AI
```python
from craft.providers import MistralProvider

provider = MistralProvider(model="mistral-large-latest")
```

### 🟢 Google Gemini
```python
from craft.providers import GoogleProvider

provider = GoogleProvider(model="gemini-2.0-flash-exp")
```

### 🟣 Anthropic Claude
```python
from craft.providers import AnthropicProvider

provider = AnthropicProvider(model="claude-sonnet-4.5")
```

### 🔵 OpenAI GPT
```python
from craft.providers import OpenAIProvider

provider = OpenAIProvider(model="gpt-4o")
```

---

## How the Debate Strategy Works

```
┌───────────────────────────────────────────┐
│  ROUND 1: Initial Opinions                │
│  Each agent gives their perspective       │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  Chairman Synthesizes                      │
│  Identifies common ground & disagreements │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  ROUND 2-N: Debate                        │
│  Agents critique synthesis & refine views │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  Chairman Checks Consensus                │
│  YES/NO based on agreement level          │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  Final Decision                            │
│  Chairman synthesizes final rationale     │
└───────────────────────────────────────────┘
```

---

## Environment Variables

```bash
# OpenRouter
export OPENROUTER_API_KEY="your-key"

# xAI
export XAI_API_KEY="your-key"

# Mistral AI
export MISTRAL_API_KEY="your-key"

# Google Gemini
export GOOGLE_API_KEY="your-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-key"

# OpenAI
export OPENAI_API_KEY="your-key"
```

---

## Why Multi-Provider?

Each provider has unique strengths:

| Provider | Best For | Example Use |
|----------|----------|-------------|
| **Gemini 2.0** | Fast synthesis, multimodal | Chairman |
| **Claude 3.5** | Deep analysis, safety | Critical reviewer |
| **GPT-4o** | Creativity, multimodal | Innovator |
| **Mistral** | European compliance (GDPR) | Privacy expert |
| **Grok** | Real-time X data | Trend analysis |
| **OpenRouter** | Cost optimization | Aggregated access |

---

## Examples

See `examples/council_demo.py` for a full working demo with the latest models!

---

## Future Enhancements

- [ ] Voting strategy (democratic consensus)
- [ ] Peer review strategy (blind review)
- [ ] Hierarchical strategy (chairman decides)
- [ ] Leaderboard generation
- [ ] Streaming debate updates
