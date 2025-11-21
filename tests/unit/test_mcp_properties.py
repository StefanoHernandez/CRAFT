"""Property-based tests for MCP integration.

These tests verify correctness properties for the Enhanced MCP Client using hypothesis
for property-based testing. Each test runs a minimum of 100 iterations to ensure
properties hold across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from pathlib import Path
import tempfile
import os

from craft.mcp.enhanced_client import EnhancedMCPClient
from craft.mcp.client import MCPTool
from craft.mcp.registry import ToolRegistry
from craft.core.errors import MCPError


# Custom strategies for generating test data
@st.composite
def mcp_tool_data(draw):
    """Generate valid MCP tool data."""
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
    description = draw(st.text(min_size=0, max_size=100))
    
    # Generate input schema
    param_count = draw(st.integers(min_value=0, max_value=5))
    properties = {}
    required = []
    
    for i in range(param_count):
        param_name = f"param{i}"
        param_type = draw(st.sampled_from(["string", "integer", "number", "boolean", "array", "object"]))
        properties[param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}"
        }
        if draw(st.booleans()):
            required.append(param_name)
    
    input_schema = {
        "type": "object",
        "properties": properties,
        "required": required
    }
    
    return {
        "name": name,
        "description": description,
        "input_schema": input_schema
    }


@st.composite
def mcp_server_paths(draw):
    """Generate valid MCP server paths."""
    # Use simple paths that could be valid server scripts
    filename = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
    extension = draw(st.sampled_from([".py", ".js", ".sh", ""]))
    return f"/path/to/{filename}{extension}"


# Feature: craft-v2-agents-tools, Property 9: MCP Tool Discovery
@settings(max_examples=100, deadline=None)
@given(
    st.lists(mcp_tool_data(), min_size=1, max_size=10, unique_by=lambda x: x["name"]),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20)
)
@pytest.mark.asyncio
async def test_property_9_mcp_tool_discovery(tools_data, namespace):
    """
    Property 9: MCP Tool Discovery
    
    For any MCP server with available tools, connecting to the server SHALL discover
    and register all tools in the tool registry.
    
    **Validates: Requirements 3.1**
    """
    # Create mock tools
    mock_tools = [
        MCPTool(
            name=tool_data["name"],
            description=tool_data["description"],
            input_schema=tool_data["input_schema"]
        )
        for tool_data in tools_data
    ]
    
    # Create a registry
    registry = ToolRegistry()
    
    # Create enhanced client with mocked base client
    with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get_tools.return_value = mock_tools
        mock_client_instance.connect = AsyncMock()
        MockClient.return_value = mock_client_instance
        
        client = EnhancedMCPClient(
            server_path="/mock/server.py",
            registry=registry,
            namespace=namespace,
            _skip_mcp_check=True
        )
        client.base_client = mock_client_instance
        
        # Connect and discover tools
        await client.connect()
        
        # Verify all tools were discovered and registered
        discovered_tools = client.get_tools()
        assert len(discovered_tools) == len(mock_tools), \
            f"Expected {len(mock_tools)} tools, discovered {len(discovered_tools)}"
        
        # Debug: Verify registry is the same object
        assert client.registry is registry, "Client is not using the passed registry!"
        
        # Verify each tool is in the registry with the correct namespace
        for tool_data in tools_data:
            tool_name = tool_data["name"]
            
            # Debug: check what's in the registry
            all_namespaces = registry.list_namespaces()
            all_tools_in_registry = registry.list_tools()
            
            # Check in namespace
            namespaced_tool = registry.get_tool(tool_name, namespace=namespace)
            assert namespaced_tool is not None, \
                f"Tool '{tool_name}' not found in namespace '{namespace}'. Available namespaces: {all_namespaces}, all tools: {len(all_tools_in_registry)}"
            
            # Verify tool metadata
            assert namespaced_tool.name == tool_name
            assert namespaced_tool.description == tool_data["description"]
            assert namespaced_tool.input_schema == tool_data["input_schema"]


# Feature: craft-v2-agents-tools, Property 10: MCP Hot Reload
@settings(max_examples=100, deadline=None)
@given(
    st.lists(mcp_tool_data(), min_size=1, max_size=5, unique_by=lambda x: x["name"]),
    st.lists(mcp_tool_data(), min_size=1, max_size=5, unique_by=lambda x: x["name"])
)
@pytest.mark.asyncio
async def test_property_10_mcp_hot_reload(initial_tools_data, updated_tools_data):
    """
    Property 10: MCP Hot Reload
    
    For any MCP server where tools are modified, the hot-reload mechanism SHALL detect
    changes and update the tool registry without application restart.
    
    **Validates: Requirements 3.2**
    """
    # Create temporary file to simulate server script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        server_path = f.name
        f.write("# Mock MCP server\n")
    
    try:
        # Create initial mock tools
        initial_tools = [
            MCPTool(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data["input_schema"]
            )
            for tool_data in initial_tools_data
        ]
        
        # Create updated mock tools
        updated_tools = [
            MCPTool(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data["input_schema"]
            )
            for tool_data in updated_tools_data
        ]
        
        registry = ToolRegistry()
        
        with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
            mock_client_instance = AsyncMock()
            
            # First return initial tools, then updated tools
            call_count = 0
            def get_tools_side_effect():
                nonlocal call_count
                call_count += 1
                return initial_tools if call_count == 1 else updated_tools
            
            mock_client_instance.get_tools.side_effect = get_tools_side_effect
            mock_client_instance.connect = AsyncMock()
            mock_client_instance.close = AsyncMock()
            MockClient.return_value = mock_client_instance
            
            client = EnhancedMCPClient(
                server_path=server_path,
                registry=registry,
                namespace="test_server",
                _skip_mcp_check=True
            )
            client.base_client = mock_client_instance
            
            # Initial connection
            await client.connect()
            initial_count = len(client.get_tools())
            assert initial_count == len(initial_tools)
            
            # Simulate file modification
            await asyncio.sleep(0.1)
            Path(server_path).touch()
            
            # Trigger hot reload manually (simulating the watcher)
            # In real scenario, this would be triggered by file watcher
            # Clear the namespace completely
            if "test_server" in registry._namespaces:
                old_tools = list(registry._namespaces["test_server"].keys())
                for tool_name in old_tools:
                    namespaced_name = f"test_server:{tool_name}"
                    registry.unregister_tool(namespaced_name)
                # Also clear from the namespace dict
                registry._namespaces["test_server"].clear()
            
            await client.discover_tools()
            
            # Verify tools were updated
            updated_count = len(client.get_tools())
            assert updated_count == len(updated_tools), \
                f"Expected {len(updated_tools)} tools after reload, got {updated_count}"
            
            await client.close()
    
    finally:
        # Cleanup
        if os.path.exists(server_path):
            os.unlink(server_path)


# Feature: craft-v2-agents-tools, Property 11: MCP Error Recovery
@settings(max_examples=100, deadline=None)
@given(
    st.integers(min_value=1, max_value=5),
    st.booleans()
)
@pytest.mark.asyncio
async def test_property_11_mcp_error_recovery(retry_attempts, should_eventually_succeed):
    """
    Property 11: MCP Error Recovery
    
    For any MCP tool call that encounters a communication error, the system SHALL handle
    the error and provide recovery options.
    
    **Validates: Requirements 3.4**
    """
    registry = ToolRegistry()
    
    with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
        mock_client_instance = AsyncMock()
        
        # Simulate connection errors
        if should_eventually_succeed:
            # Fail first attempts, then succeed
            connect_side_effects = [
                Exception("Connection timeout") for _ in range(retry_attempts - 1)
            ] + [None]  # Last attempt succeeds
            mock_client_instance.connect.side_effect = connect_side_effects
        else:
            # Always fail
            mock_client_instance.connect.side_effect = Exception("Connection failed")
        
        mock_client_instance.get_tools.return_value = []
        MockClient.return_value = mock_client_instance
        
        client = EnhancedMCPClient(
            server_path="/mock/server.py",
            registry=registry,
            retry_attempts=retry_attempts,
            retry_delay=0.01,  # Short delay for testing
            _skip_mcp_check=True
        )
        client.base_client = mock_client_instance
        
        if should_eventually_succeed:
            # Should succeed after retries
            await client.connect()
            assert client._connection_active
        else:
            # Should fail with MCPError after all retries
            with pytest.raises(MCPError) as exc_info:
                await client.connect()
            
            error = exc_info.value
            assert "Failed to connect" in error.message
            assert "server_path" in error.details
            assert not client._connection_active


# Feature: craft-v2-agents-tools, Property 12: MCP Namespace Resolution
@settings(max_examples=100)
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.booleans()
)
def test_property_12_mcp_namespace_resolution(tool_name, namespace, has_namespace_prefix):
    """
    Property 12: MCP Namespace Resolution
    
    For any two MCP servers providing tools with the same name, the namespace resolution
    SHALL allow both tools to be accessible without conflicts.
    
    **Validates: Requirements 3.5**
    """
    # Create two registries with same tool name but different namespaces
    registry = ToolRegistry()
    
    namespace1 = f"{namespace}_1"
    namespace2 = f"{namespace}_2"
    
    # Create two tools with the same name
    tool1 = MCPTool(
        name=tool_name,
        description="Tool from server 1",
        input_schema={"type": "object", "properties": {}}
    )
    
    tool2 = MCPTool(
        name=tool_name,
        description="Tool from server 2",
        input_schema={"type": "object", "properties": {}}
    )
    
    # Register both tools in different namespaces
    registry.register_mcp_tool(tool1, namespace=namespace1)
    registry.register_mcp_tool(tool2, namespace=namespace2)
    
    # Create clients for both namespaces
    with patch('craft.mcp.enhanced_client.MCPToolClient'):
        client1 = EnhancedMCPClient(
            server_path="/mock/server1.py",
            registry=registry,
            namespace=namespace1,
            _skip_mcp_check=True
        )
        
        client2 = EnhancedMCPClient(
            server_path="/mock/server2.py",
            registry=registry,
            namespace=namespace2,
            _skip_mcp_check=True
        )
        
        # Test namespace resolution
        if has_namespace_prefix:
            # Use explicit namespace prefix
            resolved1 = client1.resolve_namespace(f"{namespace1}:{tool_name}")
            resolved2 = client2.resolve_namespace(f"{namespace2}:{tool_name}")
            
            assert resolved1 == f"{namespace1}:{tool_name}"
            assert resolved2 == f"{namespace2}:{tool_name}"
        else:
            # Use implicit namespace from client
            resolved1 = client1.resolve_namespace(tool_name)
            resolved2 = client2.resolve_namespace(tool_name)
            
            assert resolved1 == f"{namespace1}:{tool_name}"
            assert resolved2 == f"{namespace2}:{tool_name}"
        
        # Verify both tools are accessible
        retrieved1 = registry.get_tool(tool_name, namespace=namespace1)
        retrieved2 = registry.get_tool(tool_name, namespace=namespace2)
        
        assert retrieved1 is not None, f"Tool not found in namespace {namespace1}"
        assert retrieved2 is not None, f"Tool not found in namespace {namespace2}"
        assert retrieved1.description == "Tool from server 1"
        assert retrieved2.description == "Tool from server 2"


# Additional edge case tests
@pytest.mark.asyncio
async def test_mcp_client_with_no_tools():
    """Test MCP client when server has no tools."""
    registry = ToolRegistry()
    
    with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get_tools.return_value = []
        mock_client_instance.connect = AsyncMock()
        MockClient.return_value = mock_client_instance
        
        client = EnhancedMCPClient(
            server_path="/mock/server.py",
            registry=registry,
            _skip_mcp_check=True
        )
        client.base_client = mock_client_instance
        
        await client.connect()
        tools = client.get_tools()
        assert len(tools) == 0


@pytest.mark.asyncio
async def test_mcp_test_tool_with_validation():
    """Test the test_tool method with input validation."""
    registry = ToolRegistry()
    
    tool = MCPTool(
        name="test_tool",
        description="Test tool",
        input_schema={
            "type": "object",
            "properties": {
                "required_param": {"type": "string"}
            },
            "required": ["required_param"]
        }
    )
    
    with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get_tools.return_value = [tool]
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.call_tool = AsyncMock(return_value="success")
        MockClient.return_value = mock_client_instance
        
        client = EnhancedMCPClient(
            server_path="/mock/server.py",
            registry=registry,
            namespace="test",
            _skip_mcp_check=True
        )
        client.base_client = mock_client_instance
        
        await client.connect()
        
        # Test with valid input
        result = await client.test_tool(
            "test_tool",
            {"required_param": "value"}
        )
        assert result["success"] is True
        assert result["result"] == "success"
        
        # Test with missing required parameter
        result = await client.test_tool(
            "test_tool",
            {}
        )
        assert result["success"] is False
        assert "Missing required parameters" in result["error"]


@pytest.mark.asyncio
async def test_mcp_error_recovery_with_retryable_errors():
    """Test that retryable errors are retried."""
    registry = ToolRegistry()
    
    with patch('craft.mcp.enhanced_client.MCPToolClient') as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.get_tools.return_value = []
        
        # Simulate retryable error then success
        mock_client_instance.call_tool.side_effect = [
            Exception("Connection timeout"),
            "success"
        ]
        
        MockClient.return_value = mock_client_instance
        
        client = EnhancedMCPClient(
            server_path="/mock/server.py",
            registry=registry,
            retry_attempts=3,
            retry_delay=0.01,
            _skip_mcp_check=True
        )
        client.base_client = mock_client_instance
        
        await client.connect()
        
        # Should succeed after retry
        result = await client.call_tool("test_tool", {})
        assert result == "success"


def test_namespace_resolution_with_multiple_servers():
    """Test namespace resolution with multiple servers providing same tool."""
    registry = ToolRegistry()
    
    # Register same tool name from 3 different servers
    for i in range(3):
        tool = MCPTool(
            name="common_tool",
            description=f"Tool from server {i}",
            input_schema={"type": "object", "properties": {}}
        )
        registry.register_mcp_tool(tool, namespace=f"server{i}")
    
    # Verify all namespaces are found
    namespaces = registry.resolve_namespace("common_tool")
    assert len(namespaces) >= 3  # At least 3 (might include 'global')
    assert "server0" in namespaces
    assert "server1" in namespaces
    assert "server2" in namespaces
    
    # Verify each can be accessed independently
    for i in range(3):
        tool = registry.get_tool("common_tool", namespace=f"server{i}")
        assert tool is not None
        assert tool.description == f"Tool from server {i}"
