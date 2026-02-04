# CRAFT: AI Developer Context & Architecture

> **🔴 STRICT SOURCE OF TRUTH** | Status: **v2.1.0-alpha** | Updated: 2026-02-04T17:20

---

## 🧭 LEGEND: How to Read & Update This File

### For AI Agents (Cursor, Windsurf, Claude, Gemini, Antigravity)

**Symbol Reference**:
*   **[!] CRITICAL**: Rules that must NEVER be broken (e.g., async usage, no print()).
*   **[?] CONTEXT**: Background info to prevent hallucinations (e.g., "Stitch" = Visual Builder).
*   **[@] PATTERN**: Mandatory coding patterns to follow (e.g., `@tool` decorator).
*   **[+] ROADMAP**: Features planned but NOT yet built - do not assume they exist.
*   **[✓] COMPLETED**: Features that are fully implemented and tested.

### 🔄 MANDATORY: End-of-Task Update Protocol

**EVERY AI agent MUST update this file at the END of each task session:**

1.  **What Changed?** Update the `Last Session Log` section with:
    - Date/time of session
    - Brief summary of changes made
    - Files modified (key ones only)
    - Any new patterns or conventions introduced

2.  **Architecture Changes?** If you added/removed modules:
    - Update **Directory Map** (Section 8)
    - Update **Architecture Pillars** (Section 2)
    - Update **Tech Stack** if new dependencies added

3.  **New Bugs Found?** Add to **Known Issues** (Section 7)

4.  **Roadmap Progress?** Move items between phases as work completes

5.  **New Vocabulary?** Add terms to **Project Dictionary** (Section 4)

> ⚠️ **IMPORTANT**: Read this file FIRST when starting a new session. Update it LAST before ending.

---

## 1. Project Identity: "The OS for AI Agents"

**CRAFT (Customizable Robotic Agent Framework & Tools)** is a production-ready, local-first Python framework for building, deploying, and orchestrating AI agents.

### Core Philosophy
*   **Goldilocks Zone**: Granular control (raw prompt access) + high-level usability (Visual Builder).
*   **Visual-First Development**: The **Stitch** interface ("n8n for AI Agents") lets users drag-and-drop logic, compiled to pure Python.
*   **Privacy & Local**: First-class support for Ollama, local embeddings, and on-premise deployment.
*   **Provider Agnostic**: 15+ LLM providers with unified interface.

### Quick Stats
| Metric | Value |
|--------|-------|
| Python Version | 3.9 - 3.12 |
| Backend LOC | ~20,600 (118 files) |
| Frontend LOC | ~3,800 (43 files) |
| LLM Providers | 15+ (OpenAI, Anthropic, Google, Groq, Mistral, Cohere, Azure, AWS, Ollama, HuggingFace, Together, Replicate, xAI, OpenRouter) |
| RAG Recall@10 | ~92% |
| License | MIT |

---

## 2. 🏛️ ARCHITECTURE PILLARS

### A. The Agent Loop (`craft/agents/`)
CRAFT Agents are **step-bounded** with explicit planning:
*   **Cycle**: `Input` → `Plan` (Optional) → `Provider.chat` → `Tool Execution` → `Output`
*   **[!] Streaming**: Every thought, tool call, and result is emitted via `EventEmitter` to WebSockets. **NEVER use `print()` for production logs.**
*   **Role Definition**: Agents must have clear `role` and `goal` defined in `AgentConfig`.
*   **Key Files**:
    - `craft/agents/agent.py` - Main Agent class (~300 LOC after refactor)
    - `craft/agents/types.py` - AgentError, ToolCall, StepResult, AgentResult
    - `craft/agents/collaboration.py` - CollaborationManager for multi-agent delegation
    - `craft/core/execution_engine.py` - Execution loop extracted from Agent

### B. The Council (`craft/consensus/`)
Multi-agent collaboration as a **governance structure**:
*   **DebateStrategy** (`debate.py`): Multi-round critique/defense cycles
*   **VotingStrategy** (`voting.py`): MAJORITY, CONSENSUS, WEIGHTED voting
*   **HierarchicalStrategy** (`hierarchical.py`): Manager → Worker delegation
*   **PeerReviewStrategy**: Cross-validation between agents

### C. The Visual Builder ("Stitch") - `stitch/`
**[?] CONTEXT**: "Stitch" is CRAFT's visual workflow builder, NOT a separate app.

*   **Frontend**: Vanilla JS (`stitch/assets/js/workflow-engine.js`) + HTML5 Canvas
*   **Entry Point**: `stitch/craft_workflow_builder/code.html`
*   **Backend Sync**: `unified-serve.py` handles WebSocket bus (`/ws`)
*   **Code Export**: `stitch/graph_parser.py` converts visual graphs → executable Python via `/api/export` (port 8001)
*   **Nexus Hub**: Landing page at `stitch/nexus-hub/` - central navigation

#### [✓] Node Taxonomy (Visual Palette)
All CRAFT capabilities exposed as draggable nodes:

| Category | Node Types | Icon Color | Description |
|----------|------------|------------|-------------|
| **Triggers** | `user_input`, `webhook`, `schedule`, `chat_trigger` | Sky | Entry points for workflows |
| **Agents** | `agent`, `planning_agent`, `research_agent`, `code_review_agent`, `content_writer_agent`, `data_analyst_agent` | Amber | AI agent instances |
| **Consensus** | `council`, `debate`, `voting`, `peer_review`, `hierarchical` | Orange | Multi-agent strategies |
| **Providers** | `openai`, `anthropic`, `google`, `groq`, `mistral`, `ollama`, `azure_openai`, `cohere` | Emerald | LLM backends |
| **Tools** | `web_search`, `calculator`, `http_request`, `read_file`, `write_file`, `database_query`, `send_email`, `custom_tool` | Blue | Agent capabilities |
| **RAG** | `document_loader`, `pdf_loader`, `text_chunker`, `embedding`, `vector_store`, `vector_search`, `hybrid_search`, `reranker`, `query_rewriter` | Teal | Retrieval pipeline |
| **Memory** | `conversation_memory`, `persistent_memory`, `context_manager` | Violet | State management |
| **Logic** | `condition`, `loop`, `switch`, `merge`, `error_handler` | Purple | Flow control |
| **Output** | `text_output`, `json_output`, `file_output`, `webhook_response` | Slate | Result handlers |

### D. The RAG Stack (`craft/rag/`)
Production-grade retrieval pipeline:
1.  **Hybrid Search**: `BM25` (keywords) + `Vector` (cosine similarity)
2.  **Reranking**: `FlashRank` cross-encoder for relevance
3.  **Query Rewriting**: LLM-based query expansion
4.  **Vector Stores**: ChromaDB, FAISS, Pinecone support

### E. Provider System (`craft/providers/`)
Unified interface for 15+ LLMs:
*   **Base**: `BaseLLMProvider` with `chat()` and `achat()` methods
*   **Retry Logic**: Exponential backoff with jitter
*   **Streaming**: All providers support token streaming
*   **[!] CRITICAL**: Always use `async/await` for LLM calls

---

## 3. 🛠️ TECH STACK

### Backend (Python)
| Component | Technology |
|-----------|------------|
| Framework | FastAPI, Pydantic v2 |
| Async | asyncio, httpx, tenacity |
| Vector DB | ChromaDB, FAISS, Pinecone |
| Storage | SQLite, PostgreSQL, Redis, MongoDB, JSON |
| Observability | Langfuse, Prometheus, OpenTelemetry, Sentry |
| Testing | pytest, Hypothesis |

### Frontend (TypeScript/JavaScript)
| Component | Technology |
|-----------|------------|
| Framework | React 18+, Vite 7.3 |
| 3D | Three.js, @react-three/fiber 9, @react-three/drei 10 |
| State | Zustand 5.0 |
| Linting | ESLint 9 (flat config) |
| Styling | Tailwind CSS, custom CSS |

---

## 4. 📚 PROJECT DICTIONARY (Anti-Hallucination)

| Term | Definition | Location |
|------|------------|----------|
| **Stitch** | Visual workflow builder interface | `stitch/` |
| **Council** | Multi-agent consensus orchestrator | `craft/consensus/` |
| **Nexus** | WebSocket event bus system | `unified-serve.py` |
| **Nexus Hub** | Central landing page UI | `stitch/nexus-hub/` |
| **GraphParser** | Converts visual graphs to Python | `stitch/graph_parser.py` |
| **Workflow Engine** | JS engine for visual graph | `stitch/assets/js/workflow-engine.js` |
| **@tool** | Decorator for defining agent tools | `craft/tools/decorators.py` |

---

## 5. [@] CODING PATTERNS & STANDARDS

### Tool Definition
**[@] PATTERN**: Use the decorator, NOT classes:
```python
from craft.tools.decorators import tool

@tool(name="my_calculator")
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b
```

### Async First
**[!] CRITICAL**: All I/O must be `async/await`. Blocking code is FORBIDDEN in `unified-serve.py`.

### Pydantic v2
**[@] PATTERN**: Use `model_config = ConfigDict()` instead of `class Config`.

### Datetime
**[@] PATTERN**: Always use `datetime.now(timezone.utc)`, NEVER `datetime.utcnow()` (deprecated).

### Retry Logic
**[@] PATTERN**: Exponential backoff with jitter:
```python
delay = (2 ** attempt) + random.uniform(0, 1)
```

### Context Loading
When building agents, always define in `system_prompt`:
1.  **Allowed Tools**: Explicit list
2.  **Working Directory**: `cwd` for scripts
3.  **Data Access**: Point to `./data` folders

---

## 6. ⛔ CONSTRAINTS (What NOT to do)

*   **No "Magic"**: Don't hide logic in abstracted base classes without logging
*   **No Heavy Dependencies**: Avoid `pandas`, `numpy` unless strictly necessary
*   **No Synchronous LLM Calls**: Never block main thread
*   **No `print()` in Production**: Use `EventEmitter` or proper logging
*   **No Hardcoded API Keys**: Use environment variables

---

## 7. 🐛 KNOWN ISSUES & TODO

### Active Issues
| Priority | Issue | Location |
|----------|-------|----------|
| MEDIUM | Replicate uses `asyncio.to_thread()` instead of native async SDK | `craft/providers/replicate.py` |
| MEDIUM | OTel bridge uses fragile `hasattr()` checks | `craft/tracing/` |
| MEDIUM | Token counting is heuristic, not using real tokenizer | `craft/core/memory.py` |
| LOW | ESLint config missing `defineConfig()` wrapper | `craft-react/eslint.config.mjs` |

### TODO
| Priority | Task |
|----------|------|
| HIGH | Implement Replicate async native with `replicate.async_run()` |
| MEDIUM | Add `defineConfig()` to ESLint config |
| MEDIUM | Consider `tiktoken` for accurate token counting |

---

## 8. 📂 DIRECTORY MAP

```
CRAFT/
├── craft/                    # Core Python framework
│   ├── agents/               # Agent loop, types, collaboration
│   ├── consensus/            # Multi-agent strategies
│   │   └── strategies/       # debate.py, voting.py, hierarchical.py
│   ├── providers/            # 15+ LLM implementations
│   ├── rag/                  # Retrieval pipeline
│   ├── tools/                # Tool definitions & decorators
│   ├── storage/              # SQLite, PostgreSQL, Redis, MongoDB adapters
│   ├── core/                 # Chatbot, Conversation, Memory, Context
│   ├── integrations/api/     # FastAPI server, WebSocket, SSE
│   └── tracing/              # OpenTelemetry bridge
├── craft-react/              # React frontend (Agent Designer)
├── stitch/                   # Visual Builder
│   ├── craft_workflow_builder/  # Main workflow builder UI
│   ├── nexus-hub/            # Landing page
│   ├── assets/js/            # workflow-engine.js
│   └── graph_parser.py       # Export API
├── .agent/                   # AI agent config
│   └── AI_CONTEXT.md         # THIS FILE
├── .aim/                     # Project memory (AIM)
│   └── memory-craft-project.jsonl
├── unified-serve.py          # Main backend entry point
└── pyproject.toml            # Python dependencies
```

---

## 9. 🗺️ DEVELOPMENT ROADMAP

### ✅ Completed (v2.0)
*   [✓] Voting & Hierarchical Strategies
*   [✓] `@tool` decorator
*   [✓] Agent decomposition (Agent.py reduced to ~300 LOC)
*   [✓] GraphParser code export
*   [✓] Node palette with 9 categories (Stitch Visual Builder)
*   [✓] Export Code button (JSON Graph → Python)

---

### 🚧 Sprint 1 - Fondamentali (In Progress)
**Focus**: Event-driven flows e validazione output

| Feature | Location | Status | Description |
|---------|----------|--------|-------------|
| **Flows System** | `craft/flows/` | [+] TODO | Event-driven workflows con `@start`, `@listen`, `@router` decorators (ispirato a CrewAI) |
| **Guardrails** | `craft/guardrails/` | [+] TODO | Validazione output con regole customizzabili, retry automatico se fallisce |

---

### 📅 Sprint 2 - Memory & State
**Focus**: Persistenza e contesto

| Feature | Location | Status | Description |
|---------|----------|--------|-------------|
| **Memory System Completo** | `craft/memory/` | [+] TODO | 4 tipi: Short-term (sessione), Long-term (persistente), Entity (knowledge graph), Contextual (RAG-based) |
| **State Checkpoints** | `craft/core/checkpoints.py` | [+] TODO | Persistenza stato workflow per resume dopo crash/interruzione |

---

### 📅 Sprint 3 - UX & Control
**Focus**: Controllo umano e orchestrazione

| Feature | Location | Status | Description |
|---------|----------|--------|-------------|
| **Human-in-the-Loop** | `craft/hitl/` | [+] TODO | Approvazione umana in workflow, pause/resume, feedback integration |
| **Process Types Unificati** | `craft/orchestration/` | [+] TODO | Unificare Sequential, Hierarchical, Consensual in API consistente |

---

### 📅 Sprint 4 - Advanced
**Focus**: State machine e deployment

| Feature | Location | Status | Description |
|---------|----------|--------|-------------|
| **Graph Execution** | `craft/graph/` | [+] TODO | State machine per workflow complessi, conditional branching, parallel execution |
| **Planning Agent Template** | `craft/agents/templates/` | [+] TODO | Agente pre-configurato per decomposizione task |
| **Auto-API** | `craft/deployment/` | [+] TODO | Wrap agents in FastAPI router automaticamente |
| **MCP UI** | `stitch/mcp-manager/` | [+] TODO | Visual manager per MCP servers |
| **Docker Templates** | `docker/` | [+] TODO | Docker Compose per deployment production |

---

## 10. 📝 LAST SESSION LOG

### 2026-02-04T17:20 (Today)
**Agent**: Gemini/Antigravity
**Summary**: Updated Stitch Visual Builder node palette and AI_CONTEXT.md
**Changes**:
- Added comprehensive node taxonomy to `code.html` (all 9 categories)
- Updated `AI_CONTEXT.md` with GraphParser info and node table
- Verified AIM memory file exists at `.aim/memory-craft-project.jsonl`

**Files Modified**:
- `stitch/craft_workflow_builder/code.html`
- `.agent/AI_CONTEXT.md`

---

## 11. 🔗 RELATED FILES

*   **AIM Memory**: `.aim/memory-craft-project.jsonl` - Detailed project knowledge graph
*   **Workflows**: `.agent/workflows/` - Reusable task workflows
*   **Dependencies**: `pyproject.toml`, `craft-react/package.json`

---

> **Remember**: This file is the single source of truth for AI agents. Keep it updated!
