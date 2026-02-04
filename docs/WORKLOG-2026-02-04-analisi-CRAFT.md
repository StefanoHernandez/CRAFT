## Analisi globale del progetto CRAFT

- **Data**: 2026-02-04  
- **Attività**: Analisi architetturale ad alto livello dell’intero progetto CRAFT (framework Python + frontend React).

### Sintesi architetturale

- **Core LLM & Chatbot**: `Chatbot` (`craft/core/chatbot.py`) orchestra provider LLM, conversazioni, memoria opzionale e motore RAG; espone API sincrone/asincrone, streaming e gestione conversazioni/memory.
- **Agenti autonomi**: `Agent` (`craft/agents/agent.py`) implementa agenti multi-step con planning opzionale, uso strumenti (`craft.tools`), memoria e collaborazione multi-agente (deleghe e council).
- **RAG & ricerca**: Modulo `craft.rag` fornisce chunking, embeddings, vector store (Chroma, FAISS, Pinecone), BM25, hybrid search con RRF e reranking per pipeline RAG a 3 stadi (query rewriting, retrieval ibrido, reranking).
- **Provider LLM**: `craft.providers` implementa astrazione unificata dei vari provider (Anthropic, OpenAI, Google, Azure, Bedrock, Cohere, ecc.) con retry/backoff, streaming normalizzato e opzioni multi-provider (es. round-robin).
- **API & integrazioni**: Moduli FastAPI sotto `craft.integrations.api` e script `unified-serve.py` espongono REST, WebSocket, SSE e widget JS/React; integrazioni con Langfuse, Prometheus, OpenTelemetry, Sentry e MCP.
- **Storage & memoria**: `craft.storage` e `craft.core.memory` gestiscono persistenza conversazioni (SQLite, Postgres, Redis, MongoDB) e migrazioni tra backend.
- **Osservabilità & monitoring**: `craft.tracing`, `craft.monitoring`, `craft.analytics` e `craft.integrations` implementano tracing a span gerarchici, health checks, logging avanzato, metriche e alerting.
- **Altri moduli chiave**: `craft.i18n` (multilingua), `craft.tools` (strumenti type-safe e MCP), `craft.consensus` (council & strategie di consenso), `craft.mcp` (server/client MCP), `craft-react` (widget React/TS) e `stitch/` (visual workflow builder).

### Note di design (rilevanza SOLID / best practice FastAPI)

- Chiare separazioni di responsabilità tra core chatbot, agenti, RAG, provider, storage e integrazioni, con uso estensivo di Pydantic e astrazioni pulite (SRP, DIP).
- Layer di provider, RAG, storage e tracing progettati per essere estendibili senza modificare i consumer (OCP) tramite interfacce/ABC e injection via costruttore.
- Lato API, l’uso di FastAPI, middleware CORS, endpoint tipizzati e integrazioni di tracing/metriche segue buone pratiche per servizi web moderni.

### Possibili miglioramenti individuati

- **Pulizia API `unified-serve.py`**:
  - Endpoint `@app.post("/api/run_node")` definito due volte con stessa logica; andrebbe consolidato in un’unica funzione per evitare ambiguità e problemi di manutenzione.
  - Esternalizzare la logica di esecuzione dei nodi (istanziazione agenti, gestione provider) in un service separato per rispettare meglio SRP e facilitare i test.

- **Separazione responsabilità in `Agent`**:
  - La classe `Agent` gestisce molte responsabilità (planning, esecuzione step, integrazione strumenti, memoria, multi‑agent delegation); si potrebbe estrarre:
    - un componente “Planner” dedicato,
    - un “ExecutionEngine” per il loop di step,
    - un “CollaborationManager” per la parte di agent‑as‑tool,
    per ridurre complessità e migliorare testabilità.

- **Heuristiche di “final answer” e step completion**:
  - I metodi `_is_final_answer` e `_is_step_complete` usano euristiche basate su substring; valutare:
    - prompt più espliciti lato LLM (es. tag strutturati per “FINAL_ANSWER”),
    - oppure un piccolo parser/format di output per ridurre falsi positivi/negativi.

- **Coerenza e type‑safety lato strumenti**:
  - Assicurarsi che tutti i `Tool` usino in modo consistente `ToolMetadata` e JSON schema, con validazione centralizzata dei parametri (già parzialmente presente in `validate_tool_choice` ma estendibile).
  - Introdurre alias di tipo e protocolli per funzione di tool, così da beneficiare di mypy/pyright in modo più forte.

- **Miglioramento best practice FastAPI**:
  - Spostare la configurazione di app, router ed event handlers in un modulo dedicato (es. `craft/api/server.py`) e usare `uvicorn` solo come entry‑point sottile.
  - Tipizzare meglio i payload (`workflow: dict`, `payload: dict`) usando Pydantic models per avere validazione e documentazione OpenAPI più ricche.

- **Osservabilità più granulare sugli agenti**:
  - Migliorare il tracciamento degli errori in `Agent.run/arun` (oggi in alcuni casi viene restituito un `AgentResult` con testo “Agent failed” senza re‑raise): si può standardizzare un modello di errore strutturato e annotare gli span con codici di errore specifici.

- **Documentazione tecnica interna**:
  - Aggiungere nei moduli chiave (`agents`, `rag`, `providers`, `storage`) brevi diagrammi o sezioni “Design decisions” per facilitare onboarding e contributi esterni.

### Fix effettuati successivamente

- **Refactor collaborazione multi‑agente**:
  - Creato `CollaborationManager` (`craft/agents/collaboration.py`) che incapsula:
    - registrazione di altri `Agent` come tool delegabili,
    - prevenzione di cicli di chiamate (call stack),
    - aggregazione dei risultati delle chiamate delegate (`agent_calls`, `total_steps`, `total_tools_used`, `total_execution_time`).
  - Aggiornata `Agent` per usare `CollaborationManager`, mantenendo compatibili le API pubbliche `can_call` e `delegate_to` e semplificando le responsabilità della classe.

- **Esecuzione e ciclo degli step**:
  - Confermato l’uso di `ExecutionEngine` (`craft/core/execution_engine.py`) per gestire il loop degli step di esecuzione, disaccoppiando la logica di loop dalla logica di business dell’agente.

- **Heuristica “final answer” migliorata**:
  - `_is_final_answer` in `Agent` ora riconosce esplicitamente il tag `<FINAL_ANSWER>` (quando il modello lo emette), con fallback alle vecchie euristiche testuali.

- **Errori strutturati negli agenti**:
  - Introdotto `AgentError` (`craft/agents/types.py`) come modello strutturato con `code`, `message` e `details`.
  - `Agent.run` ora, in caso di eccezioni non gestite, restituisce un `AgentResult` con `metadata["error"]` popolato con `AgentError.model_dump()`, invece di una semplice stringa, migliorando l’osservabilità e la possibilità di analisi a posteriori.
