# Implementation Plan - CRAFT v2.0: Agents & Advanced Tools

## Overview

This implementation plan breaks down the development of CRAFT v2.0 into discrete, manageable tasks. Each task builds incrementally on previous work, with checkpoints to ensure quality and correctness.

The plan follows an implementation-first approach: build features before writing comprehensive tests, allowing for iterative refinement based on real usage patterns.

## Task List

- [x] 1. Enhanced Tool System Foundation
  - Create base tool infrastructure with decorator, registry, and validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Implement @tool decorator with metadata extraction
  - Create `craft/tools/decorator.py` with @tool decorator
  - Extract function signature, parameters, and docstring
  - Generate JSON schema from type hints
  - Handle optional parameters and default values
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Implement ToolRegistry with registration and discovery
  - Create `craft/tools/registry.py` with ToolRegistry class
  - Implement register(), get(), list_tools() methods
  - Add get_function_schemas() for LLM provider format
  - Support namespace resolution for tool conflicts
  - _Requirements: 1.5, 3.5_

- [x] 1.3 Implement tool parameter validation
  - Add validate_args() method to Tool class
  - Validate against JSON schema before execution
  - Provide detailed validation error messages
  - _Requirements: 1.3, 15.5_

- [x] 1.4 Implement tool error handling and capture
  - Create ToolExecutionError exception class
  - Wrap tool execution with try/except
  - Capture exception details and stack traces
  - Provide error information to calling agent
  - _Requirements: 1.4, 15.1_

- [x] 1.5 Write property tests for tool system
  - **Property 1: Tool Registration Completeness**
  - **Property 2: Tool Parameter Validation**
  - **Property 3: Tool Error Capture**
  - **Property 4: Tool Registry Completeness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [x] 2. Built-in Tools Library
  - Implement common pre-built tools for immediate use
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2.1 Implement web search tools
  - Create `craft/tools/builtin/web_search.py`
  - Implement duckduckgo_search() using duckduckgo-search library
  - Implement google_search() using Google Custom Search API
  - Handle rate limiting and errors gracefully
  - _Requirements: 2.1_

- [x] 2.2 Implement calculator tool
  - Create `craft/tools/builtin/calculator.py`
  - Implement calculate() with safe expression evaluation
  - Use ast.literal_eval or similar for safety
  - Prevent code injection attacks
  - _Requirements: 2.2_

- [x] 2.3 Implement database query tool
  - Create `craft/tools/builtin/database.py`
  - Implement query_database() with parameterized queries
  - Support multiple database backends (SQLite, PostgreSQL, MySQL)
  - Prevent SQL injection through parameterization
  - _Requirements: 2.3_

- [x] 2.4 Implement HTTP request tool
  - Create `craft/tools/builtin/http.py`
  - Implement http_request() with configurable options
  - Support all HTTP methods, headers, and authentication
  - Handle timeouts and connection errors
  - _Requirements: 2.4_

- [x] 2.5 Implement file operations tools
  - Create `craft/tools/builtin/files.py`
  - Implement read_file() and write_file() with permission checks
  - Validate file paths to prevent directory traversal
  - Handle encoding and file not found errors
  - _Requirements: 2.5_

- [x] 2.6 Implement email sender tool
  - Create `craft/tools/builtin/email.py`
  - Implement send_email() with SMTP support
  - Support email templates and attachments
  - Handle SMTP authentication and errors
  - _Requirements: 2.6_

- [x] 2.7 Write property tests for built-in tools
  - **Property 5: Calculator Safety**
  - **Property 6: SQL Injection Prevention**
  - **Property 7: HTTP Request Configuration**
  - **Property 8: File Permission Respect**
  - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**


- [x] 3. MCP Integration Enhancement
  - Enhance MCP client with discovery, hot-reload, and testing utilities
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Implement MCP tool discovery
  - Create `craft/mcp/enhanced_client.py` with EnhancedMCPClient
  - Implement discover_tools() to query MCP server for available tools
  - Automatically register discovered tools in ToolRegistry
  - Handle MCP protocol communication
  - _Requirements: 3.1_

- [x] 3.2 Implement MCP hot-reload functionality
  - Add enable_hot_reload() method to EnhancedMCPClient
  - Use file system watcher to detect MCP server changes
  - Automatically re-discover and update tools on changes
  - Maintain tool state during reload
  - _Requirements: 3.2_

- [x] 3.3 Implement MCP tool testing utilities
  - Add test_tool() method for testing MCP tools with mock inputs
  - Provide validation of tool inputs and outputs
  - Generate test reports for MCP tools
  - _Requirements: 3.3_

- [x] 3.4 Implement MCP error recovery
  - Handle MCP communication protocol errors
  - Implement retry logic for transient failures
  - Provide fallback options when MCP server is unavailable
  - _Requirements: 3.4_

- [x] 3.5 Implement MCP namespace resolution
  - Add resolve_namespace() method to handle tool name conflicts
  - Support explicit namespace prefixes (e.g., "server1:tool_name")
  - Provide conflict resolution strategies
  - _Requirements: 3.5_

- [x] 3.6 Write property tests for MCP integration
  - **Property 9: MCP Tool Discovery**
  - **Property 10: MCP Hot Reload**
  - **Property 11: MCP Error Recovery**
  - **Property 12: MCP Namespace Resolution**
  - **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Autonomous Agent System Core
  - Implement the core agent execution engine
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 5.1 Implement Agent class and initialization
  - Create `craft/agents/agent.py` with Agent class
  - Implement __init__() with role, goal, backstory, tools
  - Initialize agent state and execution context
  - Set up system prompt from role and goal
  - _Requirements: 4.1_

- [x] 5.2 Implement agent execution loop
  - Implement run() method for synchronous execution
  - Create execution loop that iterates up to max_steps
  - Decide at each step: use tool, reason, or finish
  - Maintain execution state throughout
  - _Requirements: 4.2, 4.3_

- [x] 5.3 Implement tool result integration
  - Add tool results to agent's message history
  - Format tool results for LLM consumption
  - Maintain tool call records in execution state
  - _Requirements: 4.4_

- [x] 5.4 Implement agent result generation
  - Create AgentResult with final answer and metadata
  - Include all execution steps and tools used
  - Add timing and token usage information
  - _Requirements: 4.5_

- [x] 5.5 Implement max steps termination
  - Check step count at each iteration
  - Terminate gracefully when max_steps reached
  - Return partial results with explanation
  - _Requirements: 4.6_

- [x] 5.6 Implement async agent execution
  - Implement arun() method for async execution
  - Use async provider calls throughout
  - Maintain same behavior as sync version
  - _Requirements: 4.2, 4.3_

- [x] 5.7 Write property tests for agent system
  - **Property 13: Agent Initialization**
  - **Property 14: Tool Result Integration**
  - **Property 15: Agent Result Structure**
  - **Property 16: Max Steps Termination**
  - **Validates: Requirements 4.1, 4.4, 4.5, 4.6**


- [x] 6. Agent Planning System
  - Implement planning capabilities for complex tasks
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6.1 Implement plan generation
  - Create `craft/agents/planning.py` with Plan class
  - Implement generate_plan() to create initial plan from task
  - Use LLM to break down task into numbered steps
  - Store plan in agent state
  - _Requirements: 5.1_

- [x] 6.2 Implement planning interval logic
  - Add planning_interval parameter to Agent
  - Re-evaluate plan at specified step intervals
  - Update plan based on new information
  - Track plan revisions
  - _Requirements: 5.2_

- [x] 6.3 Implement step completion tracking
  - Mark steps as complete in plan
  - Proceed to next step after completion
  - Handle step failures and retries
  - _Requirements: 5.3_

- [x] 6.4 Implement plan revision
  - Detect when plan needs revision (obstacles, new info)
  - Generate revised plan using LLM
  - Maintain plan history for debugging
  - _Requirements: 5.4_

- [x] 6.5 Implement plan inspection
  - Add get_plan() method to Agent
  - Provide access to current plan and completed steps
  - Format plan for display
  - _Requirements: 5.5_

- [x] 6.6 Write property tests for planning system
  - **Property 17: Plan Generation**
  - **Property 18: Planning Interval Adherence**
  - **Property 19: Step Completion Tracking**
  - **Property 20: Plan Visibility**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

- [ ] 7. Agent Streaming
  - Implement real-time streaming of agent execution
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 7.1 Implement synchronous streaming
  - Create `craft/agents/step.py` with StepResult class
  - Implement stream_invoke() that yields StepResult objects
  - Yield after each execution step
  - Include step index, text, and tools used
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 7.2 Implement final result streaming
  - Yield final StepResult with complete answer
  - Set finished=True on final step
  - Include all execution metadata
  - _Requirements: 6.4_

- [ ] 7.3 Implement asynchronous streaming
  - Implement a_stream_invoke() as async generator
  - Use async provider calls throughout
  - Maintain same behavior as sync streaming
  - _Requirements: 6.5_

- [ ] 7.4 Write property tests for streaming
  - **Property 21: Stream Step Yielding**
  - **Property 22: Step Data Completeness**
  - **Property 23: Final Result Streaming**
  - **Property 24: Async Stream Interface**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [ ] 8. Multi-Agent Collaboration
  - Enable agents to call other agents as tools
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8.1 Implement can_call() method
  - Add can_call() to Agent class
  - Register other agents as callable tools
  - Create tool wrappers for agent calls
  - _Requirements: 7.1_

- [ ] 8.2 Implement agent-to-agent calls
  - Execute called agent and return result
  - Pass task input to called agent
  - Collect and format agent result
  - _Requirements: 7.2_

- [ ] 8.3 Implement context isolation
  - Maintain separate execution contexts per agent
  - Prevent context leakage between agents
  - Preserve agent-specific configuration
  - _Requirements: 7.3_

- [ ] 8.4 Implement recursion prevention
  - Track agent call hierarchy
  - Detect circular call patterns
  - Raise error on infinite recursion
  - _Requirements: 7.4_

- [ ] 8.5 Implement result aggregation
  - Collect results from all agents in collaboration
  - Aggregate metadata (steps, tools, timing)
  - Provide combined result to coordinator
  - _Requirements: 7.5_

- [ ] 8.6 Write property tests for multi-agent
  - **Property 25: Agent Tool Registration**
  - **Property 26: Agent Call Execution**
  - **Property 27: Context Isolation**
  - **Property 28: Recursion Prevention**
  - **Property 29: Result Aggregation**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 10. Advanced RAG - Hybrid Search
  - Implement hybrid search combining vector and BM25
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10.1 Implement HybridSearch class
  - Create `craft/rag/hybrid_search.py` with HybridSearch class
  - Initialize with vector retriever and BM25 parameters
  - Set up BM25 index structure
  - _Requirements: 8.1_

- [ ] 10.2 Implement dual indexing
  - Implement add_documents() to index in both stores
  - Tokenize documents for BM25
  - Add documents to vector store
  - _Requirements: 8.4_

- [ ] 10.3 Implement hybrid search execution
  - Implement search() method
  - Perform vector search and BM25 search in parallel
  - Collect results from both methods
  - _Requirements: 8.1_

- [ ] 10.4 Implement Reciprocal Rank Fusion
  - Implement _reciprocal_rank_fusion() method
  - Apply RRF formula to combine scores
  - Use configured weights for vector and BM25
  - _Requirements: 8.2, 8.3_

- [ ] 10.5 Implement result ranking
  - Sort combined results by relevance score
  - Return top k results
  - _Requirements: 8.5_

- [ ] 10.6 Write property tests for hybrid search
  - **Property 30: Hybrid Search Execution**
  - **Property 31: RRF Combination**
  - **Property 32: Search Weight Application**
  - **Property 33: Dual Indexing**
  - **Property 34: Combined Score Ranking**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [ ] 11. Advanced RAG - Reranking
  - Implement reranking with cross-encoder models
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 11.1 Implement Reranker class
  - Create `craft/rag/reranker.py` with Reranker class
  - Initialize with cross-encoder model
  - Load model using FlashRank
  - _Requirements: 9.1_

- [ ] 11.2 Implement reranking logic
  - Implement rerank() method
  - Score documents using cross-encoder
  - Sort by reranking scores
  - _Requirements: 9.1, 9.2_

- [ ] 11.3 Implement top-k limiting
  - Apply top_k limit to reranked results
  - Handle case where fewer results exist
  - _Requirements: 9.3_

- [ ] 11.4 Implement metadata enrichment
  - Add reranking scores to document metadata
  - Preserve original scores
  - _Requirements: 9.4_

- [ ] 11.5 Write property tests for reranking
  - **Property 35: Reranking Score Computation**
  - **Property 36: Reranking Sort Order**
  - **Property 37: Reranking Top-K Limit**
  - **Property 38: Reranking Metadata**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [ ] 12. Advanced RAG - Query Rewriting
  - Implement query rewriting techniques
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 12.1 Implement QueryRewriter class
  - Create `craft/rag/query_rewriter.py` with QueryRewriter class
  - Initialize with LLM for query generation
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 12.2 Implement query expansion
  - Implement expand_query() method
  - Generate multiple query variations using LLM
  - Return list including original query
  - _Requirements: 10.1_

- [ ] 12.3 Implement query decomposition
  - Implement decompose_query() method
  - Break complex queries into sub-queries using LLM
  - Return list of sub-queries
  - _Requirements: 10.2_

- [ ] 12.4 Implement HyDE
  - Implement hyde() method
  - Generate hypothetical document using LLM
  - Support different document lengths
  - _Requirements: 10.3_

- [ ] 12.5 Implement query clarification
  - Implement clarify_query() method
  - Rewrite ambiguous queries using LLM
  - Return clarified query
  - _Requirements: 10.4_

- [ ] 12.6 Implement multi-query retrieval
  - Integrate query rewriting with retrieval
  - Retrieve documents for all query variations
  - Combine and deduplicate results
  - _Requirements: 10.5_

- [ ] 12.7 Write property tests for query rewriting
  - **Property 39: Query Expansion Generation**
  - **Property 40: Query Decomposition**
  - **Property 41: HyDE Generation**
  - **Property 42: Query Clarification**
  - **Property 43: Multi-Query Retrieval**
  - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**


- [ ] 13. Additional LLM Providers
  - Implement support for new LLM providers
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 13.1 Implement Azure OpenAI provider
  - Create `craft/providers/azure_openai.py` with AzureOpenAIProvider
  - Support Azure endpoints and deployment names
  - Implement chat() and achat() methods
  - Support streaming
  - _Requirements: 11.1_

- [ ] 13.2 Implement AWS Bedrock provider
  - Create `craft/providers/aws_bedrock.py` with AWSBedrockProvider
  - Support Claude, Titan, Jurassic, Command, Llama models
  - Detect model family from model_id
  - Implement chat() and achat() methods
  - Support streaming
  - _Requirements: 11.2_

- [ ] 13.3 Implement Cohere provider
  - Create `craft/providers/cohere.py` with CohereProvider
  - Support Command, Command-R, Command-R-Plus models
  - Implement chat() and achat() methods
  - Support streaming and native RAG features
  - _Requirements: 11.3_

- [ ] 13.4 Implement Hugging Face provider
  - Create `craft/providers/huggingface.py` with HuggingFaceProvider
  - Support Inference API for any hosted model
  - Implement chat() and achat() methods
  - Handle model-specific formats
  - _Requirements: 11.4_

- [ ] 13.5 Implement Together AI provider
  - Create `craft/providers/together.py` with TogetherProvider
  - Support Together AI model catalog
  - Implement chat() and achat() methods
  - Support streaming
  - _Requirements: 11.5_

- [ ] 13.6 Implement Replicate provider
  - Create `craft/providers/replicate.py` with ReplicateProvider
  - Support any Replicate model
  - Implement chat() and achat() methods
  - Handle async model execution
  - _Requirements: 11.6_

- [ ] 13.7 Write property tests for provider consistency
  - **Property 44: Provider API Consistency**
  - **Validates: Requirements 11.7**

- [ ] 14. Context Tracing and Observability
  - Implement OpenTelemetry tracing for agents
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 14.1 Implement ContextTracing class
  - Create `craft/tracing/context.py` with ContextTracing class
  - Implement trace() context manager
  - Create OpenTelemetry spans for operations
  - _Requirements: 12.1, 12.5_

- [ ] 14.2 Implement agent step tracing
  - Add tracing to agent execution loop
  - Create spans for each step with timing
  - Include inputs and outputs in span attributes
  - _Requirements: 12.2_

- [ ] 14.3 Implement tool call tracing
  - Add tracing to tool execution
  - Create spans with tool name, arguments, result
  - Track tool execution time
  - _Requirements: 12.3_

- [ ] 14.4 Implement trace summary
  - Create `craft/tracing/summary.py` with TraceSummary class
  - Generate summary with spans, duration, token usage
  - Display formatted summary after trace completion
  - _Requirements: 12.4_

- [ ] 14.5 Implement detailed I/O tracing
  - Add DATAPIZZA_TRACE_CLIENT_IO environment variable support
  - Log complete request and response payloads when enabled
  - Format payloads for readability
  - _Requirements: 12.6_

- [ ] 14.6 Write property tests for tracing
  - **Property 45: Span Creation**
  - **Property 46: Step Tracing Completeness**
  - **Property 47: Tool Call Tracing**
  - **Property 48: Trace Summary Generation**
  - **Property 49: Context Manager Tracing**
  - **Property 50: Detailed I/O Logging**
  - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**

- [ ] 15. Tool Choice Control
  - Implement fine-grained control over tool usage
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 15.1 Implement tool_choice parameter
  - Add tool_choice parameter to Agent.run() and stream_invoke()
  - Support "auto", "required", "required_first", "none", and list of tool names
  - Pass tool_choice to provider
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 15.2 Implement tool filtering
  - Filter available tools based on tool_choice
  - Validate tool_choice against available tools
  - Handle invalid tool names gracefully
  - _Requirements: 13.5_

- [ ] 15.3 Write property tests for tool choice
  - **Property 51: Required Tool Use**
  - **Property 52: Required First Tool Use**
  - **Property 53: No Tool Use**
  - **Property 54: Tool Restriction**
  - **Validates: Requirements 13.2, 13.3, 13.4, 13.5**

- [ ] 16. Agent Memory Management
  - Implement conversation history and context management
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 16.1 Integrate Memory with Agent
  - Add memory parameter to Agent.__init__()
  - Save conversation history after each execution
  - Load conversation history on agent creation
  - _Requirements: 14.1, 14.2_

- [ ] 16.2 Implement message trimming
  - Trim messages when max_messages is reached
  - Preserve system prompts during trimming
  - Trim oldest user/assistant messages first
  - _Requirements: 14.3_

- [ ] 16.3 Implement persistent storage integration
  - Support all existing storage backends (SQLite, PostgreSQL, Redis, MongoDB)
  - Save conversation after each agent execution
  - Load conversation by ID
  - _Requirements: 14.4_

- [ ] 16.4 Implement memory clearing
  - Add clear_memory() method to Agent
  - Reset conversation history
  - Preserve agent configuration
  - _Requirements: 14.5_

- [ ] 16.5 Write property tests for memory
  - **Property 55: Memory Maintenance**
  - **Property 56: Message Trimming**
  - **Property 57: Persistent Storage Round-Trip**
  - **Property 58: Memory Clear Preservation**
  - **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**

- [ ] 17. Error Handling and Recovery
  - Implement robust error handling throughout
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 17.1 Implement error classes
  - Create `craft/core/errors.py` with exception hierarchy
  - Define CRAFTError, ToolExecutionError, AgentExecutionError, ProviderError
  - Include error details and context
  - _Requirements: 15.1, 15.4_

- [ ] 17.2 Implement tool error handling
  - Wrap tool execution with try/except
  - Capture and format errors for agent
  - Provide error recovery suggestions
  - _Requirements: 15.1_

- [ ] 17.3 Implement retry logic
  - Add retry decorator to provider calls
  - Configure retry attempts and backoff
  - Distinguish retryable vs non-retryable errors
  - _Requirements: 15.3_

- [ ] 17.4 Implement graceful termination
  - Handle max retry exceeded
  - Generate detailed error reports
  - Return partial results when possible
  - _Requirements: 15.3_

- [ ] 17.5 Write property tests for error handling
  - **Property 59: Tool Error Capture**
  - **Property 60: Graceful Termination**
  - **Property 61: Provider Error Messages**
  - **Property 62: Validation Error Quality**
  - **Validates: Requirements 15.1, 15.3, 15.4, 15.5**

- [ ] 18. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Documentation and Examples
  - Create comprehensive documentation and examples
  - Update README with new features
  - Create migration guide from v1.x to v2.0

- [ ] 19.1 Update README.md
  - Add Agent system examples
  - Add Tool system examples
  - Add Multi-agent collaboration examples
  - Add Advanced RAG examples
  - Update provider list

- [ ] 19.2 Create examples directory
  - Create `examples/agents/` with agent examples
  - Create `examples/tools/` with custom tool examples
  - Create `examples/multi_agent/` with collaboration examples
  - Create `examples/advanced_rag/` with RAG examples

- [ ] 19.3 Create migration guide
  - Document breaking changes from v1.x
  - Provide migration examples
  - Create MIGRATION.md file

- [ ] 19.4 Update API documentation
  - Generate API docs from docstrings
  - Create developer guide
  - Add troubleshooting section

