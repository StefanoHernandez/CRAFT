# CRAFT: AI Developer Context & Architecture

> **STRICT SOURCE OF TRUTH** | Status: **v2.1.0-alpha** | Updated: 2026-02-04

---

## 🧭 LEGEND: How to Read This File
**For AI Agents (Cursor, Windsurf, Claude, Gemini)**:
*   **[!] CRITICAL**: Rules that must never be broken (e.g., async usage).
*   **[?] CONTEXT**: Background info to prevent hallucinations (e.g., "Stitch" = Frontend).
*   **[@] PATTERN**: Mandatory coding patterns (e.g., `@tool` decorator).
*   **[+] ROADMAP**: Features planned but not yet built.

## 🛠️ META: Maintenance & Updates
**When to Update**:
1.  **Architecture Change**: If you add a new module (e.g., "Observability"), add it to **Directory Map** and **Architecture Pillars**.
2.  **New Pattern**: If a better way to do things emerges (e.g., "Use Pydantic v3"), update **Coding Patterns** and mark the old one as **Deprecated**.
3.  **Roadmap Progress**: Move items from **Roadmap** to **Completed** when finished.

**Process**:
*   Always read this file *first* when starting a new session.
*   If you make a structural change, update this file *last* as part of your "Definition of Done".

---

## 1. Project Identity: "The OS for AI Agents"
**CRAFT (Customizable Robotic Agent Framework & Tools)** is a proprietary, local-first framework designed to be the definitive platform for building, deploying, and observing AI agents.

### Core Philosophy
*   **Goldilocks Zone**: We reject the "Black Box" of generic frameworks. We offer **granular control** (raw prompt access) wrapped in **high-level usability** (Visual Builder).
*   **Visual-First Development**: Agents shouldn't just be code. The **Stitch** interface ("n8n for Agents") allows users to drag-and-drop logic, which we then **compile to pure Python**.
*   **Privacy & Local**: First-class support for Ollama and Local Embeddings. We don't force the cloud.

---

## 2. 🏛️ ARCHITECTURE PILLARS

### A. The Agent Loop (`craft.agents`)
CRAFT Agents are **step-bounded** with explicit planning:
*   **Cycle**: `Input` -> `Plan` (Optional) -> `Provider.chat` -> `Tool Execution` -> `Output`.
*   **[!] Streaming**: Every thought, tool call, and result is emitted via `EventEmitter` to WebSockets. **Do not use `print()` for production logs.**
*   **Role Definition**: Agents must have clear `Role` ("Researcher") and `Goal` ("Analyze data") defined in `AgentConfig` to constrain the LLM.

### B. The Council (`craft.consensus`)
Multi-agent collaboration is a **governance structure**, not a chatroom.
*   **DebateStrategy**: Agents perform multi-round critique rounds.
*   **VotingStrategy**: Democratic resolution (Majority, Consensus, Weighted).
*   **HierarchicalStrategy**: Explicit `Manager` -> `Worker` delegation.

### C. The Visual Builder ("Stitch")
Lives in `stitch/`. It is **NOT** a separate app; it's deeply integrated.
*   **Frontend**: Vanilla JS (`workflow-engine.js`) + HTML5 Canvas. Fast, dependency-free.
*   **Backend Sync**: `unified-serve.py` handles the WebSocket bus (`/ws`).
*   **Execution**: The frontend *simulates* flow, but the backend *executes* standard Python code.

### D. The RAG Stack
We built a production-grade RAG pipeline from scratch:
1.  **Hybrid Search**: `BM25` (Keywords) + `Vector` (Cosine Similarity).
2.  **Reranking**: `FlashRank` (Cross-Encoder) re-orders results for relevance.
3.  **Query Rewriting**: LLM-based query expansion before search.

---

## 3. 📚 PROJECT DICTIONARY (Anti-Hallucination)
*   **Stitch**: The name of CRAFT's Visual Builder interface. Code is in `stitch/`.
*   **Council**: The module handling multi-agent consensus (`craft.consensus`).
*   **Workflow Engine**: The JS engine running the visual graph (`workflow-engine.js`).
*   **Nexus**: The WebSocket event bus system.
*   **Decorators**: Refers to `craft.tools.decorators` (specifically `@tool`).

---

## 4. [@] CODING PATTERNS & STANDARDS

### Tool Definition
**Do Not** write `class MyTool(Tool): ...` for simple functions.
**Do** use the decorator:
```python
from craft.tools.decorators import tool

@tool(name="my_calculator")
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b
```

### Async First
**[!] CRITICAL**: All I/O (LLM calls, DB, Tools) must be `async/await`. Blocking code is forbidden in `unified-serve.py`.

### Context Loading (Best Practice)
When building new agents, use `system_prompt` to provide:
1.  **Allowed Tools**: Explicitly list what the agent can use.
2.  **Working Directory**: If the agent runs scripts, define `cwd`.
3.  **Data Access**: Point to specific `./data` folders.

---

## 5. ⛔ CONSTRAINTS (What NOT to do)
*   **No "Magic"**: Do not hide logic in abstracted base classes without logging.
*   **No Heavy dependencies**: Do not add imports (like `pandas` or `numpy`) unless strictly necessary for a specific tool.
*   **No Synchronous LLM Calls**: Never block the main thread waiting for an LLM response.

---

## 6. 🗺️ DEVELOPMENT ROADMAP

### ✅ Phase 1: Core Framework (Completed)
*   Voting & Hierarchical Strategies implemented.
*   `@tool` decorator active.

### 🚧 Phase 2: Visual Builder Upgrade (In Progress)
*   **[+] Export Code**: Button to convert JSON Graph -> `agent.py`.
*   **[+] Partial Execution**: "Right-click -> Execute Node" to test prompts.

### 📅 Phase 3: Deployment
*   **[+] Auto-API**: Wrap agents in a FastAPI router automatically.
*   **[+] MCP UI**: Visual manager for MCP servers.

---

## 7. 📂 DIRECTORY MAP
*   `craft/agents/`: Core logic (`agent.py`).
*   `craft/consensus/`: Strategies (`debate.py`, `voting.py`, `hierarchical.py`).
*   `craft/tools/`: Definitions & decorators.
*   `stitch/`: Visual Builder (Frontend).
*   `unified-serve.py`: Main backend entry point.
