# Design Document - CRAFT v2.0: Agents & Advanced Tools

## Overview

CRAFT v2.0 introduces a comprehensive agent system that enables autonomous, multi-step task execution with flexible tool integration. This design builds upon CRAFT's existing foundation while adding capabilities inspired by DataPizza AI, CrewAI, and LangGraph.

### Key Design Goals

1. **Simplicity First**: Maintain CRAFT's philosophy of easy integration while adding powerful features
2. **Provider Agnostic**: Support all LLM providers with consistent API
3. **Extensibility**: Make it trivial to add custom tools and integrate external systems
4. **Observability**: Built-in tracing and monitoring for production deployments
5. **Performance**: Efficient execution with streaming and async support
6. **Reliability**: Robust error handling and graceful degradation

### Architecture Principles

- **Modular Design**: Each component (agents, tools, RAG, providers) is independent
- **Composition Over Inheritance**: Favor mixins and composition for flexibility
- **Type Safety**: Full type hints and Pydantic models throughout
- **Async First**: Support both sync and async APIs
- **Backward Compatible**: Existing CRAFT code continues to work

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CRAFT v2.0 System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Agents     │  │    Tools     │  │     RAG      │    │
│  │              │  │              │  │              │    │
│  │ - Agent      │  │ - @tool      │  │ - Hybrid     │    │
│  │ - Planning   │  │ - Registry   │  │ - Reranking  │    │
│  │ - Streaming  │  │ - Built-ins  │  │ - Query      │    │
│  │ - Memory     │  │ - MCP        │  │   Rewriting  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
│                   ┌────────▼────────┐                      │
│                   │   Core Engine   │                      │
│                   │                 │                      │
│                   │ - Execution     │                      │
│                   │ - State Mgmt    │                      │
│                   │ - Error Handle  │                      │
│                   └────────┬────────┘                      │
│                            │                               │
│         ┌──────────────────┼──────────────────┐            │
│         │                  │                  │            │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐   │
│  │  Providers  │  │   Observability │  │  Storage   │   │
│  │             │  │                 │  │            │   │
│  │ - Anthropic │  │ - Tracing       │  │ - SQLite   │   │
│  │ - OpenAI    │  │ - Metrics       │  │ - Postgres │   │
│  │ - Azure     │  │ - Logging       │  │ - Redis    │   │
│  │ - Bedrock   │  │ - Langfuse      │  │ - MongoDB  │   │
│  └─────────────┘  └─────────────────┘  └────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```


## Components and Interfaces

### 1. Agent System

#### Agent Class

```python
from typing import Optional, List, Dict, Any, Union, AsyncIterator
from pydantic import BaseModel, Field
from craft.providers.base import Provider
from craft.tools.base import Tool
from craft.core.memory import Memory

class AgentConfig(BaseModel):
    """Configuration for an Agent."""
    name: str
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    max_steps: int = Field(default=10, ge=1, le=100)
    planning_interval: Optional[int] = Field(default=None, ge=1)
    terminate_on_text: bool = True
    verbose: bool = False

class StepResult(BaseModel):
    """Result of a single agent execution step."""
    index: int
    text: str
    tools_used: List[ToolCall] = Field(default_factory=list)
    finished: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    """Final result from agent execution."""
    text: str
    steps: List[StepResult]
    total_steps: int
    tools_used: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Agent:
    """
    Autonomous agent that can reason and execute multi-step tasks.
    
    Inspired by DataPizza AI's simplicity and CrewAI's role-based design.
    """
    
    def __init__(
        self,
        name: str,
        provider: Provider,
        role: Optional[str] = None,
        goal: Optional[str] = None,
        backstory: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        max_steps: int = 10,
        planning_interval: Optional[int] = None,
        memory: Optional[Union[bool, Memory]] = None,
        verbose: bool = False
    ):
        """Initialize agent with configuration."""
        pass
    
    def run(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs
    ) -> AgentResult:
        """Execute task and return final result."""
        pass
    
    def stream_invoke(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs
    ) -> Iterator[StepResult]:
        """Stream execution steps in real-time."""
        pass
    
    async def arun(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs
    ) -> AgentResult:
        """Async version of run."""
        pass
    
    async def a_stream_invoke(
        self,
        task_input: str,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs
    ) -> AsyncIterator[StepResult]:
        """Async version of stream_invoke."""
        pass
    
    def can_call(self, agents: List["Agent"]) -> None:
        """Register other agents as callable tools."""
        pass
```


### 2. Tool System

#### Tool Decorator and Base Classes

```python
from typing import Callable, Any, Dict, Optional
from pydantic import BaseModel, Field
from inspect import signature, Parameter
import functools

class ToolParameter(BaseModel):
    """Parameter definition for a tool."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Any = None

class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str
    json_schema: Dict[str, Any]

class Tool(BaseModel):
    """Base tool class."""
    name: str
    description: str
    func: Callable
    metadata: ToolMetadata
    
    def __call__(self, **kwargs) -> Any:
        """Execute the tool."""
        return self.func(**kwargs)
    
    def validate_args(self, **kwargs) -> Dict[str, Any]:
        """Validate arguments against schema."""
        pass

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    """
    Decorator to register a function as a tool.
    
    Example:
        @tool
        def search_web(query: str) -> str:
            '''Search the web for information.'''
            return search_results
    """
    def decorator(func: Callable) -> Tool:
        # Extract metadata from function
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or ""
        
        # Generate JSON schema from signature
        sig = signature(func)
        parameters = []
        for param_name, param in sig.parameters.items():
            parameters.append(ToolParameter(
                name=param_name,
                type=str(param.annotation),
                required=param.default == Parameter.empty,
                default=param.default if param.default != Parameter.empty else None
            ))
        
        metadata = ToolMetadata(
            name=tool_name,
            description=tool_desc,
            parameters=parameters,
            return_type=str(sig.return_annotation),
            json_schema=_generate_json_schema(sig)
        )
        
        return Tool(
            name=tool_name,
            description=tool_desc,
            func=func,
            metadata=metadata
        )
    
    return decorator

class ToolRegistry:
    """Central registry for all tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """Get function schemas for LLM providers."""
        return [tool.metadata.json_schema for tool in self._tools.values()]
```


### 3. Built-in Tools Library

```python
# craft/tools/builtin/web_search.py
@tool
def duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web using DuckDuckGo."""
    pass

@tool
def google_search(query: str, max_results: int = 5, api_key: str = None) -> List[Dict[str, str]]:
    """Search the web using Google Custom Search API."""
    pass

# craft/tools/builtin/calculator.py
@tool
def calculate(expression: str) -> float:
    """Safely evaluate mathematical expressions."""
    pass

# craft/tools/builtin/database.py
@tool
def query_database(sql: str, params: Dict[str, Any] = None, connection_string: str = None) -> List[Dict]:
    """Execute parameterized SQL query."""
    pass

# craft/tools/builtin/http.py
@tool
def http_request(
    url: str,
    method: str = "GET",
    headers: Dict[str, str] = None,
    body: Any = None,
    auth: Dict[str, str] = None
) -> Dict[str, Any]:
    """Make HTTP request with configurable options."""
    pass

# craft/tools/builtin/files.py
@tool
def read_file(path: str, encoding: str = "utf-8") -> str:
    """Read file contents with permission checks."""
    pass

@tool
def write_file(path: str, content: str, encoding: str = "utf-8") -> bool:
    """Write content to file with permission checks."""
    pass

# craft/tools/builtin/email.py
@tool
def send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: str = None,
    smtp_config: Dict[str, Any] = None
) -> bool:
    """Send email via SMTP with template support."""
    pass
```

### 4. MCP Integration

```python
# craft/mcp/enhanced_client.py
class EnhancedMCPClient:
    """Enhanced MCP client with discovery and hot-reload."""
    
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.tools: Dict[str, Tool] = {}
        self._watcher = None
    
    async def connect(self) -> None:
        """Connect to MCP server and discover tools."""
        pass
    
    async def discover_tools(self) -> List[Tool]:
        """Discover all available tools from server."""
        pass
    
    async def enable_hot_reload(self) -> None:
        """Enable automatic tool reloading on server changes."""
        pass
    
    async def test_tool(self, tool_name: str, mock_input: Dict[str, Any]) -> Any:
        """Test an MCP tool with mock input."""
        pass
    
    def resolve_namespace(self, tool_name: str, namespace: str = None) -> str:
        """Resolve tool name with namespace to avoid conflicts."""
        pass
```


### 5. Advanced RAG Components

```python
# craft/rag/hybrid_search.py
class HybridSearch:
    """Combines dense (vector) and sparse (BM25) retrieval."""
    
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        rrf_k: int = 60
    ):
        self.vector_retriever = vector_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        self.bm25_index = None
    
    def add_documents(self, documents: List[Document]) -> None:
        """Index documents in both vector store and BM25."""
        pass
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Perform hybrid search with RRF fusion."""
        pass

# craft/rag/reranker.py
class Reranker:
    """Rerank search results using cross-encoder models."""
    
    def __init__(self, model: str = "ms-marco-MiniLM-L-12-v2"):
        self.model = model
        self.ranker = None
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Document]:
        """Rerank documents by relevance."""
        pass

# craft/rag/query_rewriter.py
class QueryRewriter:
    """Rewrite queries for better retrieval."""
    
    def __init__(self, llm: Any):
        self.llm = llm
    
    def expand_query(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate query variations."""
        pass
    
    def decompose_query(self, query: str) -> List[str]:
        """Break complex query into sub-queries."""
        pass
    
    def hyde(self, query: str) -> str:
        """Generate hypothetical document."""
        pass
    
    def clarify_query(self, query: str) -> str:
        """Clarify ambiguous query."""
        pass
```

### 6. Additional Providers

```python
# craft/providers/azure_openai.py
class AzureOpenAIProvider(Provider):
    """Azure OpenAI Service provider."""
    
    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
        **kwargs
    ):
        pass

# craft/providers/aws_bedrock.py
class AWSBedrockProvider(Provider):
    """AWS Bedrock provider supporting multiple model families."""
    
    def __init__(
        self,
        model_id: str,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        **kwargs
    ):
        pass

# craft/providers/cohere.py
class CohereProvider(Provider):
    """Cohere provider with native RAG support."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "command-r-plus",
        **kwargs
    ):
        pass
```


## Data Models

### Agent Execution State

```python
class AgentState(BaseModel):
    """State maintained during agent execution."""
    task_input: str
    current_step: int
    max_steps: int
    messages: List[Message]
    tools_used: List[ToolCall]
    plan: Optional[Plan] = None
    finished: bool = False
    result: Optional[str] = None

class Plan(BaseModel):
    """Agent's execution plan."""
    steps: List[str]
    current_step_index: int
    completed_steps: List[int]
    created_at: datetime
    updated_at: datetime

class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None
    timestamp: datetime
```

### Tracing Models

```python
class TraceSpan(BaseModel):
    """OpenTelemetry span for tracing."""
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    attributes: Dict[str, Any]
    status: str  # "ok", "error"

class TraceSummary(BaseModel):
    """Summary of a trace execution."""
    trace_id: str
    total_spans: int
    duration_seconds: float
    token_usage: Dict[str, int]  # {model: {prompt: X, completion: Y}}
    errors: List[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Tool System Properties

Property 1: Tool Registration Completeness
*For any* valid Python function decorated with @tool, the tool registry SHALL contain an entry with complete metadata including name, description, and parameter schema.
**Validates: Requirements 1.1, 1.2**

Property 2: Tool Parameter Validation
*For any* registered tool and any input arguments, validation against the tool's JSON schema SHALL either succeed with valid parameters or fail with specific validation errors.
**Validates: Requirements 1.3, 15.5**

Property 3: Tool Error Capture
*For any* tool execution that raises an exception, the system SHALL capture the exception details and make them available to the calling agent.
**Validates: Requirements 1.4**

Property 4: Tool Registry Completeness
*For any* set of registered tools, querying the registry SHALL return all tools with their complete descriptions and parameters.
**Validates: Requirements 1.5**

Property 5: Calculator Safety
*For any* mathematical expression string, the calculator tool SHALL evaluate it safely without executing arbitrary code.
**Validates: Requirements 2.2**

Property 6: SQL Injection Prevention
*For any* SQL query with user-provided parameters, the database tool SHALL use parameterization to prevent SQL injection attacks.
**Validates: Requirements 2.3**

Property 7: HTTP Request Configuration
*For any* HTTP request with specified headers, method, and authentication, the HTTP tool SHALL make the request with exactly those configurations.
**Validates: Requirements 2.4**

Property 8: File Permission Respect
*For any* file operation, the file tool SHALL respect system permissions and fail gracefully when permissions are insufficient.
**Validates: Requirements 2.5**

### MCP Integration Properties

Property 9: MCP Tool Discovery
*For any* MCP server with available tools, connecting to the server SHALL discover and register all tools in the tool registry.
**Validates: Requirements 3.1**

Property 10: MCP Hot Reload
*For any* MCP server where tools are modified, the hot-reload mechanism SHALL detect changes and update the tool registry without application restart.
**Validates: Requirements 3.2**

Property 11: MCP Error Recovery
*For any* MCP tool call that encounters a communication error, the system SHALL handle the error and provide recovery options.
**Validates: Requirements 3.4**

Property 12: MCP Namespace Resolution
*For any* two MCP servers providing tools with the same name, the namespace resolution SHALL allow both tools to be accessible without conflicts.
**Validates: Requirements 3.5**


### Agent System Properties

Property 13: Agent Initialization
*For any* valid agent configuration with role and goal, agent initialization SHALL create an agent with appropriate context and capabilities.
**Validates: Requirements 4.1**

Property 14: Tool Result Integration
*For any* agent step where a tool is used, the tool result SHALL be incorporated into the agent's message history for the next step.
**Validates: Requirements 4.4**

Property 15: Agent Result Structure
*For any* completed agent execution, the result SHALL contain the final answer and execution metadata including steps and tools used.
**Validates: Requirements 4.5**

Property 16: Max Steps Termination
*For any* agent execution that reaches max_steps, the system SHALL terminate gracefully and return partial results with an explanation.
**Validates: Requirements 4.6**

Property 17: Plan Generation
*For any* agent that receives a task, if planning is enabled, the system SHALL generate an initial plan with numbered steps.
**Validates: Requirements 5.1**

Property 18: Planning Interval Adherence
*For any* agent with planning_interval configured, the system SHALL re-evaluate the plan at exactly those step intervals.
**Validates: Requirements 5.2**

Property 19: Step Completion Tracking
*For any* agent with a plan, when a step is completed, the system SHALL mark it as complete and proceed to the next step.
**Validates: Requirements 5.3**

Property 20: Plan Visibility
*For any* agent execution in progress, the current plan and completed steps SHALL be accessible for inspection.
**Validates: Requirements 5.5**

### Streaming Properties

Property 21: Stream Step Yielding
*For any* agent execution using stream_invoke, the system SHALL yield a StepResult object for each execution step.
**Validates: Requirements 6.1**

Property 22: Step Data Completeness
*For any* streamed StepResult, it SHALL contain step index, reasoning text, and list of tools used.
**Validates: Requirements 6.2, 6.3**

Property 23: Final Result Streaming
*For any* agent execution that completes, the final streamed item SHALL be a complete result with the answer.
**Validates: Requirements 6.4**

Property 24: Async Stream Interface
*For any* agent execution using a_stream_invoke, the system SHALL provide an async generator that yields StepResult objects.
**Validates: Requirements 6.5**

### Multi-Agent Properties

Property 25: Agent Tool Registration
*For any* agent A that calls can_call with agents [B, C], agents B and C SHALL appear as callable tools in A's tool registry.
**Validates: Requirements 7.1**

Property 26: Agent Call Execution
*For any* agent A that calls agent B, agent B SHALL execute and return its result to agent A.
**Validates: Requirements 7.2**

Property 27: Context Isolation
*For any* two agents A and B where A calls B, each agent SHALL maintain separate execution contexts that do not interfere.
**Validates: Requirements 7.3**

Property 28: Recursion Prevention
*For any* circular agent call pattern (A calls B, B calls A), the system SHALL detect and prevent infinite recursion.
**Validates: Requirements 7.4**

Property 29: Result Aggregation
*For any* multi-agent collaboration, the system SHALL aggregate results from all agents involved.
**Validates: Requirements 7.5**


### Advanced RAG Properties

Property 30: Hybrid Search Execution
*For any* query with hybrid search enabled, the system SHALL perform both vector search and BM25 search.
**Validates: Requirements 8.1**

Property 31: RRF Combination
*For any* hybrid search with results from both methods, the system SHALL combine them using the Reciprocal Rank Fusion algorithm.
**Validates: Requirements 8.2**

Property 32: Search Weight Application
*For any* hybrid search with configured weights, the system SHALL apply those weights to vector and BM25 scores in the fusion calculation.
**Validates: Requirements 8.3**

Property 33: Dual Indexing
*For any* documents added to hybrid search, they SHALL be indexed in both the vector store and BM25 index.
**Validates: Requirements 8.4**

Property 34: Combined Score Ranking
*For any* hybrid search results, documents SHALL be ranked in descending order by their combined relevance scores.
**Validates: Requirements 8.5**

Property 35: Reranking Score Computation
*For any* search results with reranking enabled, the system SHALL compute relevance scores using the cross-encoder model.
**Validates: Requirements 9.1**

Property 36: Reranking Sort Order
*For any* reranked results, documents SHALL be sorted in descending order by reranking score.
**Validates: Requirements 9.2**

Property 37: Reranking Top-K Limit
*For any* reranking with top_k specified, exactly k results SHALL be returned (or fewer if fewer results exist).
**Validates: Requirements 9.3**

Property 38: Reranking Metadata
*For any* reranked document, the reranking score SHALL be added to the document's metadata.
**Validates: Requirements 9.4**

Property 39: Query Expansion Generation
*For any* query with expansion enabled, the system SHALL generate multiple query variations using the LLM.
**Validates: Requirements 10.1**

Property 40: Query Decomposition
*For any* complex query with decomposition enabled, the system SHALL break it into simpler sub-queries.
**Validates: Requirements 10.2**

Property 41: HyDE Generation
*For any* query with HyDE enabled, the system SHALL generate a hypothetical document that answers the query.
**Validates: Requirements 10.3**

Property 42: Query Clarification
*For any* ambiguous query with clarification enabled, the system SHALL rewrite it to be more specific.
**Validates: Requirements 10.4**

Property 43: Multi-Query Retrieval
*For any* rewritten queries, the system SHALL retrieve documents for all query variations and combine the results.
**Validates: Requirements 10.5**

### Provider Properties

Property 44: Provider API Consistency
*For any* two different providers, the chat and streaming methods SHALL have the same interface and behavior.
**Validates: Requirements 11.7**

### Observability Properties

Property 45: Span Creation
*For any* agent operation with tracing enabled, the system SHALL create an OpenTelemetry span.
**Validates: Requirements 12.1**

Property 46: Step Tracing Completeness
*For any* traced agent step, the span SHALL include timing, inputs, and outputs.
**Validates: Requirements 12.2**

Property 47: Tool Call Tracing
*For any* tool call with tracing enabled, a span SHALL be created with tool name, arguments, and result.
**Validates: Requirements 12.3**

Property 48: Trace Summary Generation
*For any* completed trace, the system SHALL display a summary with total spans, duration, and token usage.
**Validates: Requirements 12.4**

Property 49: Context Manager Tracing
*For any* operations within a trace context manager, all operations SHALL be automatically captured in spans.
**Validates: Requirements 12.5**

Property 50: Detailed I/O Logging
*For any* operation with detailed I/O tracing enabled, complete request and response payloads SHALL be logged.
**Validates: Requirements 12.6**

### Tool Choice Properties

Property 51: Required Tool Use
*For any* agent execution with tool_choice="required", at least one tool SHALL be used during execution.
**Validates: Requirements 13.2**

Property 52: Required First Tool Use
*For any* agent execution with tool_choice="required_first", a tool SHALL be used on the first step.
**Validates: Requirements 13.3**

Property 53: No Tool Use
*For any* agent execution with tool_choice="none", no tools SHALL be used during execution.
**Validates: Requirements 13.4**

Property 54: Tool Restriction
*For any* agent execution with tool_choice as a list of tool names, only those specific tools SHALL be available for use.
**Validates: Requirements 13.5**

### Memory Properties

Property 55: Memory Maintenance
*For any* agent with memory enabled, conversation history SHALL be maintained across multiple task executions.
**Validates: Requirements 14.1, 14.2**

Property 56: Message Trimming
*For any* agent memory that reaches max_messages, older messages SHALL be trimmed while system prompts are preserved.
**Validates: Requirements 14.3**

Property 57: Persistent Storage Round-Trip
*For any* agent with persistent storage, conversation history SHALL be saved and loaded correctly across sessions.
**Validates: Requirements 14.4**

Property 58: Memory Clear Preservation
*For any* agent memory clear operation, conversation history SHALL be reset while agent configuration remains unchanged.
**Validates: Requirements 14.5**

### Error Handling Properties

Property 59: Tool Error Capture
*For any* tool execution that fails, the exception SHALL be captured and provided to the agent.
**Validates: Requirements 15.1**

Property 60: Graceful Termination
*For any* agent that exceeds max retry attempts, the system SHALL terminate gracefully with a detailed error report.
**Validates: Requirements 15.3**

Property 61: Provider Error Messages
*For any* provider API failure, the system SHALL provide clear error messages or fallback options.
**Validates: Requirements 15.4**

Property 62: Validation Error Quality
*For any* validation failure, the system SHALL return specific validation errors with suggestions for correction.
**Validates: Requirements 15.5**


## Error Handling

### Error Categories

1. **Tool Errors**: Tool execution failures, validation errors, permission errors
2. **Agent Errors**: Max steps exceeded, planning failures, reasoning errors
3. **Provider Errors**: API failures, rate limits, authentication errors
4. **MCP Errors**: Connection failures, protocol errors, tool discovery failures
5. **RAG Errors**: Retrieval failures, embedding errors, index errors

### Error Handling Strategy

```python
class CRAFTError(Exception):
    """Base exception for CRAFT errors."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ToolExecutionError(CRAFTError):
    """Tool execution failed."""
    pass

class AgentExecutionError(CRAFTError):
    """Agent execution failed."""
    pass

class ProviderError(CRAFTError):
    """Provider API error."""
    pass

# Error recovery in agents
class Agent:
    def _handle_tool_error(self, error: ToolExecutionError) -> str:
        """Provide error information to agent for recovery."""
        error_message = f"Tool execution failed: {error.message}"
        if error.details:
            error_message += f"\nDetails: {json.dumps(error.details)}"
        return error_message
    
    def _handle_max_steps(self) -> AgentResult:
        """Handle graceful termination at max steps."""
        return AgentResult(
            text="Task incomplete: Maximum steps reached",
            steps=self.state.steps,
            total_steps=self.state.current_step,
            tools_used=[call.tool_name for call in self.state.tools_used],
            metadata={"terminated": "max_steps", "partial": True}
        )
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class Agent:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _call_provider_with_retry(self, messages: List[Message]) -> ChatResponse:
        """Call provider with automatic retry on transient failures."""
        try:
            return await self.provider.achat(messages)
        except ProviderError as e:
            if e.details.get("retryable"):
                raise  # Will be retried
            else:
                # Non-retryable error, fail immediately
                raise AgentExecutionError(
                    f"Provider error: {e.message}",
                    details=e.details
                )
```

## Testing Strategy

### Unit Testing

Unit tests will cover:
- Tool decorator and registration
- Tool validation logic
- Agent initialization
- Step execution logic
- Memory management
- Error handling paths
- Provider interface compliance

### Property-Based Testing

Property-based tests will verify the correctness properties defined above using the `hypothesis` library for Python.

**Testing Framework**: `hypothesis` (Python property-based testing)
**Test Configuration**: Minimum 100 iterations per property test

Each property-based test will be tagged with a comment referencing the design document:

```python
# Feature: craft-v2-agents-tools, Property 1: Tool Registration Completeness
@given(st.functions())
def test_tool_registration_completeness(func):
    """Test that any valid function decorated with @tool is registered completely."""
    tool = tool_decorator(func)
    assert tool.name in registry
    assert tool.metadata is not None
    assert tool.metadata.parameters is not None
```

### Integration Testing

Integration tests will cover:
- End-to-end agent execution with real LLM providers
- MCP server integration
- RAG pipeline with real vector stores
- Multi-agent collaboration scenarios
- Streaming functionality

### Performance Testing

Performance benchmarks will measure:
- Tool execution overhead
- Agent step latency
- Streaming throughput
- Memory usage
- RAG retrieval speed

