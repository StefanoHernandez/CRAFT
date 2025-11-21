# Requirements Document - CRAFT v2.0: Agents & Advanced Tools

## Introduction

CRAFT v2.0 introduces a comprehensive agent system with advanced tool capabilities, enabling developers to easily integrate intelligent chatbots into any website. This phase focuses on building the foundation for autonomous agents, flexible tool integration, enhanced RAG capabilities, and additional LLM provider support.

The system must maintain CRAFT's core philosophy of simplicity while adding powerful multi-agent orchestration capabilities inspired by DataPizza AI, CrewAI, and LangGraph.

## Glossary

- **Agent**: An autonomous AI entity with a specific role, goal, and set of tools that can execute multi-step tasks
- **Tool**: A function that an agent can call to perform actions (search, calculate, query databases, etc.)
- **Tool Registry**: A centralized system for managing and discovering available tools
- **MCP (Model Context Protocol)**: A protocol for exposing and consuming tools across different systems
- **RAG (Retrieval-Augmented Generation)**: A technique combining retrieval from knowledge bases with LLM generation
- **Hybrid Search**: A search method combining dense (vector) and sparse (BM25) retrieval
- **Reranking**: A process to reorder search results based on relevance using cross-encoder models
- **Query Rewriting**: Techniques to reformulate queries for better retrieval (expansion, decomposition, HyDE)
- **Planning**: The process where an agent breaks down complex tasks into manageable steps
- **Step**: A single action or reasoning iteration in an agent's execution
- **Provider**: An LLM service provider (Anthropic, OpenAI, Google, Azure, AWS, etc.)
- **Streaming**: Real-time delivery of agent execution steps and responses
- **Context Tracing**: Observability system for tracking agent execution with OpenTelemetry

## Requirements

### Requirement 1: Enhanced Tool System

**User Story:** As a developer, I want to easily create and integrate custom tools for my agents, so that I can extend chatbot capabilities without complex setup.

#### Acceptance Criteria

1. WHEN a developer defines a function with the @tool decorator THEN the system SHALL automatically register the tool with proper metadata extraction
2. WHEN a tool is registered THEN the system SHALL validate the function signature and generate JSON schema for parameters
3. WHEN an agent executes a tool THEN the system SHALL validate input parameters against the tool's schema before execution
4. WHEN a tool execution fails THEN the system SHALL capture the error and provide detailed debugging information to the agent
5. WHEN a developer queries available tools THEN the system SHALL return a list of all registered tools with their descriptions and parameters

### Requirement 2: Built-in Tools Library

**User Story:** As a developer, I want access to common pre-built tools, so that I can quickly add standard functionality without writing custom code.

#### Acceptance Criteria

1. WHEN a developer imports the web search tool THEN the system SHALL provide DuckDuckGo and Google search capabilities
2. WHEN a developer uses the calculator tool THEN the system SHALL evaluate mathematical expressions safely
3. WHEN a developer uses the database query tool THEN the system SHALL execute SQL queries with parameterization to prevent injection
4. WHEN a developer uses the HTTP request tool THEN the system SHALL make HTTP calls with configurable headers, methods, and authentication
5. WHEN a developer uses the file operations tool THEN the system SHALL read, write, and manipulate files with proper permission checks
6. WHEN a developer uses the email sender tool THEN the system SHALL send emails via SMTP with template support

### Requirement 3: MCP Integration Enhancement

**User Story:** As a developer, I want seamless integration with MCP servers, so that I can leverage external tools and services easily.

#### Acceptance Criteria

1. WHEN a developer adds an MCP server THEN the system SHALL automatically discover and register all available tools from that server
2. WHEN an MCP server updates its tools THEN the system SHALL support hot-reloading without restarting the application
3. WHEN a developer tests an MCP tool THEN the system SHALL provide testing utilities with mock inputs and validation
4. WHEN an MCP tool is called THEN the system SHALL handle communication protocol and error recovery automatically
5. WHEN multiple MCP servers provide similar tools THEN the system SHALL allow namespace resolution to avoid conflicts

### Requirement 4: Autonomous Agent System

**User Story:** As a developer, I want to create autonomous agents that can reason and execute multi-step tasks, so that I can build intelligent assistants that solve complex problems.

#### Acceptance Criteria

1. WHEN a developer creates an agent with a role and goal THEN the system SHALL initialize the agent with appropriate context and capabilities
2. WHEN an agent receives a task THEN the system SHALL autonomously plan and execute multiple steps to complete the task
3. WHEN an agent executes a step THEN the system SHALL decide whether to use a tool, reason, or provide a final answer
4. WHEN an agent uses a tool THEN the system SHALL incorporate the tool result into its reasoning for the next step
5. WHEN an agent completes a task THEN the system SHALL return a structured result with the final answer and execution metadata
6. WHEN an agent reaches max_steps limit THEN the system SHALL terminate gracefully and return partial results with explanation

### Requirement 5: Agent Planning System

**User Story:** As a developer, I want agents to create and follow plans for complex tasks, so that execution is more structured and debuggable.

#### Acceptance Criteria

1. WHEN an agent receives a complex task THEN the system SHALL generate an initial plan with numbered steps
2. WHEN a planning_interval is configured THEN the system SHALL re-evaluate and update the plan at specified intervals
3. WHEN an agent completes a planned step THEN the system SHALL mark the step as complete and proceed to the next step
4. WHEN an agent encounters an obstacle THEN the system SHALL revise the plan to adapt to new information
5. WHEN a developer inspects agent execution THEN the system SHALL provide access to the current plan and completed steps

### Requirement 6: Agent Streaming

**User Story:** As a developer, I want to stream agent execution in real-time, so that users can see the agent's thought process and actions as they happen.

#### Acceptance Criteria

1. WHEN a developer calls stream_invoke on an agent THEN the system SHALL yield StepResult objects for each execution step
2. WHEN an agent executes a step THEN the system SHALL stream the step index, reasoning text, and tools used
3. WHEN an agent uses a tool THEN the system SHALL stream the tool name, arguments, and result
4. WHEN an agent completes execution THEN the system SHALL stream a final result with the complete answer
5. WHEN streaming is used asynchronously THEN the system SHALL provide an async generator for non-blocking iteration

### Requirement 7: Multi-Agent Collaboration

**User Story:** As a developer, I want agents to collaborate by calling other specialized agents, so that I can build systems where agents work together on complex tasks.

#### Acceptance Criteria

1. WHEN a developer calls can_call on an agent with a list of other agents THEN the system SHALL register those agents as callable tools
2. WHEN an agent calls another agent THEN the system SHALL execute the called agent and return its result
3. WHEN an agent calls another agent THEN the system SHALL maintain separate execution contexts for each agent
4. WHEN nested agent calls occur THEN the system SHALL track the call hierarchy and prevent infinite recursion
5. WHEN an agent collaboration completes THEN the system SHALL aggregate results from all agents involved

### Requirement 8: Advanced RAG - Hybrid Search

**User Story:** As a developer, I want to combine dense and sparse retrieval methods, so that I can improve search quality over single-method approaches.

#### Acceptance Criteria

1. WHEN a developer enables hybrid search THEN the system SHALL perform both vector search and BM25 search
2. WHEN both search methods return results THEN the system SHALL combine them using Reciprocal Rank Fusion
3. WHEN a developer configures search weights THEN the system SHALL apply the specified weights to vector and BM25 scores
4. WHEN documents are added to hybrid search THEN the system SHALL index them in both vector store and BM25 index
5. WHEN hybrid search is queried THEN the system SHALL return results ranked by combined relevance scores

### Requirement 9: Advanced RAG - Reranking

**User Story:** As a developer, I want to rerank search results using cross-encoder models, so that the most relevant documents appear first.

#### Acceptance Criteria

1. WHEN a developer enables reranking THEN the system SHALL use a cross-encoder model to score document relevance
2. WHEN search results are reranked THEN the system SHALL sort documents by reranking scores in descending order
3. WHEN a developer specifies top_k for reranking THEN the system SHALL return only the top k reranked results
4. WHEN reranking is applied THEN the system SHALL add reranking scores to document metadata
5. WHEN a developer selects a reranking model THEN the system SHALL support multiple models (MiniLM, MultiBERT, T5)

### Requirement 10: Advanced RAG - Query Rewriting

**User Story:** As a developer, I want to automatically improve queries before retrieval, so that search results are more relevant and comprehensive.

#### Acceptance Criteria

1. WHEN a developer enables query expansion THEN the system SHALL generate multiple query variations using an LLM
2. WHEN a developer enables query decomposition THEN the system SHALL break complex queries into simpler sub-queries
3. WHEN a developer enables HyDE THEN the system SHALL generate hypothetical documents that answer the query
4. WHEN a developer enables query clarification THEN the system SHALL rewrite ambiguous queries to be more specific
5. WHEN rewritten queries are used THEN the system SHALL retrieve documents for all query variations and combine results

### Requirement 11: Additional LLM Providers

**User Story:** As a developer, I want support for more LLM providers, so that I can choose the best model for my use case and budget.

#### Acceptance Criteria

1. WHEN a developer uses Azure OpenAI provider THEN the system SHALL support Azure endpoints with deployment-based model selection
2. WHEN a developer uses AWS Bedrock provider THEN the system SHALL support Claude, Titan, Jurassic, Command, and Llama models
3. WHEN a developer uses Cohere provider THEN the system SHALL support Command, Command-R, and Command-R-Plus models
4. WHEN a developer uses Hugging Face provider THEN the system SHALL support inference API for any hosted model
5. WHEN a developer uses Together AI provider THEN the system SHALL support their model catalog with streaming
6. WHEN a developer uses Replicate provider THEN the system SHALL support any model available on Replicate
7. WHEN a provider is used THEN the system SHALL maintain consistent API across all providers for chat and streaming

### Requirement 12: Context Tracing and Observability

**User Story:** As a developer, I want detailed tracing of agent execution, so that I can debug issues and monitor performance in production.

#### Acceptance Criteria

1. WHEN a developer enables context tracing THEN the system SHALL create OpenTelemetry spans for all agent operations
2. WHEN an agent executes THEN the system SHALL trace each step with timing, inputs, and outputs
3. WHEN a tool is called THEN the system SHALL create a span with tool name, arguments, and result
4. WHEN tracing completes THEN the system SHALL display a summary with total spans, duration, and token usage
5. WHEN a developer uses a trace context manager THEN the system SHALL automatically capture all operations within the context
6. WHEN detailed I/O tracing is enabled THEN the system SHALL log complete request and response payloads

### Requirement 13: Tool Choice Control

**User Story:** As a developer, I want fine-grained control over when agents use tools, so that I can optimize for different scenarios.

#### Acceptance Criteria

1. WHEN tool_choice is set to "auto" THEN the system SHALL let the agent decide when to use tools
2. WHEN tool_choice is set to "required" THEN the system SHALL force the agent to use at least one tool
3. WHEN tool_choice is set to "required_first" THEN the system SHALL require tool use on the first step only
4. WHEN tool_choice is set to "none" THEN the system SHALL prevent the agent from using any tools
5. WHEN tool_choice is a list of tool names THEN the system SHALL restrict the agent to only those specific tools

### Requirement 14: Agent Memory Management

**User Story:** As a developer, I want agents to maintain conversation history and context, so that they can have coherent multi-turn interactions.

#### Acceptance Criteria

1. WHEN an agent is created with memory enabled THEN the system SHALL maintain a conversation history
2. WHEN an agent executes multiple tasks THEN the system SHALL preserve context across task executions
3. WHEN memory reaches max_messages limit THEN the system SHALL trim older messages while preserving system prompts
4. WHEN an agent uses persistent storage THEN the system SHALL save and load conversation history across sessions
5. WHEN a developer clears agent memory THEN the system SHALL reset conversation history while preserving agent configuration

### Requirement 15: Error Handling and Recovery

**User Story:** As a developer, I want robust error handling in agents and tools, so that failures are graceful and debuggable.

#### Acceptance Criteria

1. WHEN a tool execution fails THEN the system SHALL capture the exception and provide it to the agent for recovery
2. WHEN an agent encounters an error THEN the system SHALL attempt to recover by revising its approach
3. WHEN max retry attempts are exceeded THEN the system SHALL terminate gracefully with a detailed error report
4. WHEN a provider API fails THEN the system SHALL provide fallback options or clear error messages
5. WHEN validation fails THEN the system SHALL return specific validation errors with suggestions for correction

