"""Enhanced MCP Client with discovery, hot-reload, and testing utilities."""

from typing import Any, Dict, List, Optional, Callable
import asyncio
from pathlib import Path

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from craft.mcp.client import MCPTool, MCPToolClient
from craft.mcp.registry import ToolRegistry
from craft.utils.logging import get_logger
from craft.core.errors import MCPError


class EnhancedMCPClient:
    """
    Enhanced MCP client with discovery, hot-reload, and testing utilities.
    
    Extends the basic MCPToolClient with advanced features:
    - Automatic tool discovery and registration
    - Hot-reload on server changes
    - Tool testing with mock inputs
    - Error recovery and retry logic
    - Namespace resolution for tool conflicts
    """

    def __init__(
        self,
        server_path: str,
        registry: Optional[ToolRegistry] = None,
        namespace: Optional[str] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        _skip_mcp_check: bool = False  # For testing purposes
    ):
        """
        Initialize enhanced MCP client.

        Args:
            server_path: Path to MCP server script/executable
            registry: Optional ToolRegistry for automatic registration
            namespace: Optional namespace for tools from this server
            retry_attempts: Number of retry attempts for transient failures
            retry_delay: Delay between retries in seconds
            _skip_mcp_check: Internal flag to skip MCP availability check (for testing)
        """
        if not _skip_mcp_check and not MCP_AVAILABLE:
            raise ImportError(
                "mcp package not installed. "
                "Install with: pip install 'craft-chatbot[mcp]'"
            )

        self.server_path = server_path
        self.registry = registry if registry is not None else ToolRegistry()
        self.namespace = namespace or Path(server_path).stem
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self.logger = get_logger("craft.mcp.enhanced_client")
        self.base_client = None if _skip_mcp_check else MCPToolClient(server_path)
        self._watcher = None
        self._hot_reload_enabled = False
        self._connection_active = False

    async def connect(self) -> None:
        """
        Connect to MCP server and discover tools.
        
        Automatically discovers all available tools and registers them
        in the tool registry with the configured namespace.
        
        Raises:
            MCPError: If connection fails after all retry attempts
        """
        await self._connect_with_retry()
        await self.discover_tools()

    async def _connect_with_retry(self) -> None:
        """Connect to MCP server with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(
                    f"Connecting to MCP server (attempt {attempt + 1}/{self.retry_attempts}): "
                    f"{self.server_path}"
                )
                await self.base_client.connect()
                self._connection_active = True
                self.logger.info(f"Successfully connected to MCP server: {self.server_path}")
                return
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Connection attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # All attempts failed
        raise MCPError(
            message=f"Failed to connect to MCP server after {self.retry_attempts} attempts",
            details={
                "server_path": self.server_path,
                "last_error": str(last_error)
            }
        )

    async def discover_tools(self) -> List[MCPTool]:
        """
        Discover all available tools from the MCP server.
        
        Queries the MCP server for its tool list and automatically
        registers all discovered tools in the tool registry with
        the configured namespace.
        
        Returns:
            List of discovered MCPTool instances
            
        Raises:
            MCPError: If tool discovery fails
        """
        if not self._connection_active:
            raise MCPError(
                message="Not connected to MCP server",
                details={"server_path": self.server_path}
            )
        
        try:
            self.logger.info(f"Discovering tools from MCP server: {self.server_path}")
            
            # Get tools from base client
            tools_result = self.base_client.get_tools()
            # Handle both sync and async returns (for testing compatibility)
            if hasattr(tools_result, '__await__'):
                tools = await tools_result
            else:
                tools = tools_result
            
            # Register each tool in the registry with namespace
            for tool in tools:
                self.registry.register_mcp_tool(tool, namespace=self.namespace)
                self.logger.debug(
                    f"Registered tool '{tool.name}' in namespace '{self.namespace}'"
                )
            
            self.logger.info(
                f"Discovered and registered {len(tools)} tools from "
                f"'{self.namespace}' namespace"
            )
            
            return tools
            
        except Exception as e:
            raise MCPError(
                message=f"Tool discovery failed: {str(e)}",
                details={
                    "server_path": self.server_path,
                    "namespace": self.namespace
                }
            )

    async def enable_hot_reload(self, watch_interval: float = 2.0) -> None:
        """
        Enable automatic tool reloading on server changes.
        
        Uses a file system watcher to detect changes to the MCP server
        and automatically re-discovers and updates tools when changes occur.
        
        Args:
            watch_interval: Interval in seconds to check for changes
            
        Note:
            This is a simple polling-based implementation. For production use,
            consider using a proper file system watcher like watchdog.
        """
        if self._hot_reload_enabled:
            self.logger.warning("Hot reload already enabled")
            return
        
        self._hot_reload_enabled = True
        self.logger.info(f"Enabling hot reload for {self.server_path}")
        
        # Start background task to watch for changes
        asyncio.create_task(self._watch_for_changes(watch_interval))

    async def _watch_for_changes(self, interval: float) -> None:
        """Background task to watch for server changes."""
        server_file = Path(self.server_path)
        last_modified = server_file.stat().st_mtime if server_file.exists() else 0
        
        while self._hot_reload_enabled:
            try:
                await asyncio.sleep(interval)
                
                if not server_file.exists():
                    continue
                
                current_modified = server_file.stat().st_mtime
                
                if current_modified > last_modified:
                    self.logger.info(f"Detected changes in {self.server_path}, reloading tools...")
                    
                    # Unregister old tools from this namespace
                    old_tools = self.registry._namespaces.get(self.namespace, {})
                    for tool_name in list(old_tools.keys()):
                        namespaced_name = f"{self.namespace}:{tool_name}"
                        self.registry.unregister_tool(namespaced_name)
                    
                    # Reconnect and rediscover
                    try:
                        await self.base_client.close()
                        await self._connect_with_retry()
                        await self.discover_tools()
                        self.logger.info("Hot reload completed successfully")
                    except Exception as e:
                        self.logger.error(f"Hot reload failed: {e}")
                    
                    last_modified = current_modified
                    
            except Exception as e:
                self.logger.error(f"Error in hot reload watcher: {e}")

    def disable_hot_reload(self) -> None:
        """Disable hot reload functionality."""
        self._hot_reload_enabled = False
        self.logger.info("Hot reload disabled")

    async def test_tool(
        self,
        tool_name: str,
        mock_input: Dict[str, Any],
        validate_output: Optional[Callable[[Any], bool]] = None
    ) -> Dict[str, Any]:
        """
        Test an MCP tool with mock inputs.
        
        Executes the tool with provided mock inputs and optionally validates
        the output. Useful for testing tool behavior before using in production.
        
        Args:
            tool_name: Name of the tool to test (can include namespace prefix)
            mock_input: Dictionary of mock input arguments
            validate_output: Optional function to validate the output
            
        Returns:
            Dictionary containing test results:
                - success: Whether the test passed
                - result: Tool execution result
                - error: Error message if test failed
                - validation_passed: Whether output validation passed (if validator provided)
                
        Example:
            result = await client.test_tool(
                "search",
                {"query": "test query"},
                validate_output=lambda x: isinstance(x, str) and len(x) > 0
            )
        """
        self.logger.info(f"Testing tool '{tool_name}' with mock input: {mock_input}")
        
        test_result = {
            "success": False,
            "result": None,
            "error": None,
            "validation_passed": None
        }
        
        try:
            # Resolve tool name with namespace if needed
            resolved_name = self.resolve_namespace(tool_name)
            
            # Get tool from registry (resolved_name already includes namespace)
            tool = self.registry.get_tool(resolved_name)
            if not tool:
                test_result["error"] = f"Tool '{tool_name}' not found"
                return test_result
            
            # Validate input against tool schema
            try:
                # Basic validation - check required parameters
                required_params = tool.input_schema.get("required", [])
                missing_params = [p for p in required_params if p not in mock_input]
                if missing_params:
                    test_result["error"] = f"Missing required parameters: {missing_params}"
                    return test_result
            except Exception as e:
                test_result["error"] = f"Input validation failed: {e}"
                return test_result
            
            # Execute tool
            result = await self.base_client.call_tool(resolved_name, mock_input)
            test_result["result"] = result
            test_result["success"] = True
            
            # Validate output if validator provided
            if validate_output:
                try:
                    validation_passed = validate_output(result)
                    test_result["validation_passed"] = validation_passed
                    if not validation_passed:
                        test_result["error"] = "Output validation failed"
                        test_result["success"] = False
                except Exception as e:
                    test_result["validation_passed"] = False
                    test_result["error"] = f"Output validation error: {e}"
                    test_result["success"] = False
            
            self.logger.info(f"Tool test completed: {test_result['success']}")
            
        except Exception as e:
            test_result["error"] = str(e)
            self.logger.error(f"Tool test failed: {e}")
        
        return test_result

    def resolve_namespace(self, tool_name: str) -> str:
        """
        Resolve tool name with namespace to handle conflicts.
        
        If the tool name includes a namespace prefix (e.g., "server1:tool_name"),
        returns it as-is. Otherwise, prepends the client's namespace.
        
        Args:
            tool_name: Tool name (with or without namespace prefix)
            
        Returns:
            Fully qualified tool name with namespace
            
        Example:
            # If namespace is "myserver"
            resolve_namespace("search") -> "myserver:search"
            resolve_namespace("other:search") -> "other:search"
        """
        if ":" in tool_name:
            # Already has namespace prefix
            return tool_name
        else:
            # Add this client's namespace
            return f"{self.namespace}:{tool_name}"

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retry_on_error: bool = True
    ) -> Any:
        """
        Call an MCP tool with error recovery.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            retry_on_error: Whether to retry on transient errors
            
        Returns:
            Tool execution result
            
        Raises:
            MCPError: If tool execution fails after all retries
        """
        resolved_name = self.resolve_namespace(tool_name)
        
        if not retry_on_error:
            return await self.base_client.call_tool(resolved_name, arguments)
        
        # Call with retry logic
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                result = await self.base_client.call_tool(resolved_name, arguments)
                return result
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Tool call attempt {attempt + 1} failed: {e}"
                )
                
                # Check if error is retryable
                if self._is_retryable_error(e) and attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    break
        
        # All attempts failed
        raise MCPError(
            message=f"Tool execution failed after {self.retry_attempts} attempts",
            details={
                "tool_name": resolved_name,
                "arguments": arguments,
                "last_error": str(last_error)
            }
        )

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is likely transient and retryable
        """
        # Common retryable error patterns
        retryable_patterns = [
            "timeout",
            "connection",
            "network",
            "temporary",
            "unavailable"
        ]
        
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in retryable_patterns)

    async def close(self) -> None:
        """Close connection to MCP server."""
        self.disable_hot_reload()
        await self.base_client.close()
        self._connection_active = False
        self.logger.info(f"Closed connection to MCP server: {self.server_path}")

    def get_tools(self) -> List[MCPTool]:
        """Get list of available tools from this client."""
        namespace_tools = self.registry._namespaces.get(self.namespace, {})
        return list(namespace_tools.values())

    def __repr__(self) -> str:
        return (
            f"EnhancedMCPClient(server={self.server_path}, "
            f"namespace={self.namespace}, "
            f"tools={len(self.get_tools())}, "
            f"hot_reload={self._hot_reload_enabled})"
        )
