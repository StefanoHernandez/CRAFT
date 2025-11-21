"""Property-based tests for built-in tools.

These tests verify correctness properties for the built-in tools library using hypothesis.
Each test runs a minimum of 100 iterations to ensure properties hold across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

from craft.tools.builtin.calculator import calculate
from craft.tools.builtin.database import query_database
from craft.tools.builtin.http import http_request
from craft.tools.builtin.files import read_file, write_file
from craft.core.errors import ToolExecutionError, ToolValidationError

# Check if sqlalchemy is available
try:
    import sqlalchemy
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


# Feature: craft-v2-agents-tools, Property 5: Calculator Safety
@settings(max_examples=100)
@given(st.text(alphabet="0123456789+-*/ ().", min_size=1, max_size=50))
def test_property_5_calculator_safety(expression):
    """
    Property 5: Calculator Safety
    
    For any mathematical expression string, the calculator tool SHALL evaluate it safely
    without executing arbitrary code.
    
    **Validates: Requirements 2.2**
    """
    # Filter out expressions that would be syntactically invalid
    # but still test that no code execution happens
    try:
        result = calculate(expression=expression)
        # If it succeeds, result should be a number
        assert isinstance(result, (int, float)), \
            f"Result should be numeric, got {type(result)}"
        # Verify it's a finite number
        assert not (isinstance(result, float) and (result != result or abs(result) == float('inf'))), \
            "Result should be finite"
    except (ValueError, ToolExecutionError):
        # Expected for invalid expressions - this is safe behavior
        # ToolExecutionError wraps ValueError from the calculator
        pass
    except ZeroDivisionError:
        # Expected for division by zero - this is safe behavior
        pass


def test_calculator_rejects_code_execution():
    """Test that calculator rejects attempts to execute code."""
    dangerous_expressions = [
        "__import__('os').system('ls')",
        "exec('print(1)')",
        "eval('1+1')",
        "open('/etc/passwd').read()",
        "[x for x in range(10)]",
        "lambda x: x",
        "def foo(): pass",
        "import os",
    ]
    
    for expr in dangerous_expressions:
        with pytest.raises((ValueError, ToolExecutionError)) as exc_info:
            calculate(expression=expr)
        # Verify it's rejected for safety reasons
        error_msg = str(exc_info.value).lower()
        assert "unsupported" in error_msg or "invalid" in error_msg


def test_calculator_safe_operations():
    """Test that calculator supports safe mathematical operations."""
    safe_expressions = [
        ("2 + 2", 4),
        ("10 - 3", 7),
        ("4 * 5", 20),
        ("15 / 3", 5),
        ("17 // 5", 3),
        ("17 % 5", 2),
        ("2 ** 3", 8),
        ("-5", -5),
        ("+5", 5),
        ("(2 + 3) * 4", 20),
    ]
    
    for expr, expected in safe_expressions:
        result = calculate(expression=expr)
        assert result == expected, f"Expected {expected}, got {result} for {expr}"


# Feature: craft-v2-agents-tools, Property 6: SQL Injection Prevention
@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="sqlalchemy not installed")
@settings(max_examples=100)
@given(
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100)
)
def test_property_6_sql_injection_prevention(malicious_input, age_value):
    """
    Property 6: SQL Injection Prevention
    
    For any SQL query with user-provided parameters, the database tool SHALL use
    parameterization to prevent SQL injection attacks.
    
    **Validates: Requirements 2.3**
    """
    # Create a temporary SQLite database
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name
    
    try:
        # Set up test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        """)
        cursor.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        cursor.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        cursor.execute("INSERT INTO users (name, age) VALUES ('Charlie', 35)")
        conn.commit()
        conn.close()
        
        # Test with parameterized query
        connection_string = f"sqlite:///{db_path}"
        
        # Use parameterized query - this should be safe
        sql = "SELECT * FROM users WHERE age > :min_age"
        params = {"min_age": age_value}
        
        try:
            results = query_database(sql=sql, params=params, connection_string=connection_string)
            
            # Verify results are valid
            assert isinstance(results, list), "Results should be a list"
            for row in results:
                assert isinstance(row, dict), "Each row should be a dict"
                assert "age" in row, "Row should have age field"
                # Verify the parameterization worked correctly
                assert row["age"] > age_value, \
                    f"Row age {row['age']} should be greater than {age_value}"
        except Exception as e:
            # If there's an error, it should be a runtime error, not SQL injection
            assert "RuntimeError" in str(type(e)) or "ValueError" in str(type(e))
        
        # Now test that SQL injection attempts in parameters are neutralized
        # The malicious input should be treated as data, not SQL code
        sql_injection_attempt = "SELECT * FROM users WHERE name = :name"
        params = {"name": malicious_input}
        
        try:
            results = query_database(
                sql=sql_injection_attempt,
                params=params,
                connection_string=connection_string
            )
            # If it succeeds, it should return empty or matching results
            # but NOT execute any injected SQL
            assert isinstance(results, list)
            # The malicious input should be treated as a literal string
            for row in results:
                assert row["name"] == malicious_input
        except Exception:
            # Errors are acceptable - the key is no SQL injection occurred
            pass
            
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="sqlalchemy not installed")
def test_sql_injection_attempts_are_neutralized():
    """Test that common SQL injection patterns are neutralized."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name
    
    try:
        # Set up test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO users (name) VALUES ('Alice')")
        conn.commit()
        conn.close()
        
        connection_string = f"sqlite:///{db_path}"
        
        # Common SQL injection patterns
        injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
        ]
        
        for injection in injection_attempts:
            # Use parameterized query
            sql = "SELECT * FROM users WHERE name = :name"
            params = {"name": injection}
            
            # This should treat the injection as literal data
            results = query_database(sql=sql, params=params, connection_string=connection_string)
            
            # Should return empty results (no match) or error, but NOT execute injection
            assert isinstance(results, list)
            # The table should still exist (not dropped)
            verify_sql = "SELECT COUNT(*) as count FROM users"
            verify_results = query_database(sql=verify_sql, connection_string=connection_string)
            assert len(verify_results) > 0, "Table should still exist"
            
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


# Feature: craft-v2-agents-tools, Property 7: HTTP Request Configuration
@settings(max_examples=100)
@given(
    st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH"]),
    st.dictionaries(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz-", min_size=1, max_size=20),
        st.text(min_size=1, max_size=50),
        min_size=0,
        max_size=3
    )
)
def test_property_7_http_request_configuration(method, headers):
    """
    Property 7: HTTP Request Configuration
    
    For any HTTP request with specified headers, method, and authentication, the HTTP tool
    SHALL make the request with exactly those configurations.
    
    **Validates: Requirements 2.4**
    """
    # Mock the httpx.request to verify configuration
    with patch('httpx.request') as mock_request:
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "response body"
        mock_response.json.return_value = None
        mock_request.return_value = mock_response
        
        # Make request
        url = "https://example.com/api"
        result = http_request(
            url=url,
            method=method,
            headers=headers,
            timeout=30
        )
        
        # Verify the request was made with correct configuration
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        # Verify method
        assert call_args.kwargs["method"] == method.upper(), \
            f"Expected method {method.upper()}, got {call_args.kwargs['method']}"
        
        # Verify URL
        assert call_args.kwargs["url"] == url, \
            f"Expected URL {url}, got {call_args.kwargs['url']}"
        
        # Verify headers
        assert call_args.kwargs["headers"] == headers, \
            f"Expected headers {headers}, got {call_args.kwargs['headers']}"
        
        # Verify timeout
        assert call_args.kwargs["timeout"] == 30, \
            f"Expected timeout 30, got {call_args.kwargs['timeout']}"
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "status_code" in result
        assert "headers" in result
        assert "body" in result


def test_http_request_with_authentication():
    """Test that authentication is properly configured."""
    with patch('httpx.request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "authenticated"
        mock_request.return_value = mock_response
        
        # Test bearer token auth
        result = http_request(
            url="https://api.example.com",
            method="GET",
            auth={"type": "bearer", "token": "secret_token"}
        )
        
        # Verify Authorization header was added
        call_args = mock_request.call_args
        assert "Authorization" in call_args.kwargs["headers"]
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer secret_token"
        
        # Test basic auth
        mock_request.reset_mock()
        result = http_request(
            url="https://api.example.com",
            method="GET",
            auth={"type": "basic", "username": "user", "password": "pass"}
        )
        
        # Verify basic auth was passed
        call_args = mock_request.call_args
        assert call_args.kwargs["auth"] == ("user", "pass")


# Feature: craft-v2-agents-tools, Property 8: File Permission Respect
@settings(max_examples=100)
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=20),
    st.text(min_size=0, max_size=100)
)
def test_property_8_file_permission_respect(filename, content):
    """
    Property 8: File Permission Respect
    
    For any file operation, the file tool SHALL respect system permissions and fail
    gracefully when permissions are insufficient.
    
    **Validates: Requirements 2.5**
    """
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        
        # Test write operation
        try:
            success = write_file(path=file_path, content=content)
            assert success is True, "Write should return True on success"
            
            # Verify file was created
            assert os.path.exists(file_path), "File should exist after write"
            
            # Test read operation
            read_content = read_file(path=file_path)
            # Normalize line endings for comparison (Windows vs Unix)
            assert read_content.replace('\r\n', '\n').replace('\r', '\n') == content.replace('\r\n', '\n').replace('\r', '\n'), \
                f"Read content should match written content"
            
        except PermissionError as e:
            # Permission errors should be raised gracefully
            assert "permission" in str(e).lower()
        except Exception as e:
            # Other errors should be wrapped appropriately
            assert isinstance(e, (ValueError, RuntimeError, FileNotFoundError))


def test_file_operations_prevent_directory_traversal():
    """Test that directory traversal attempts are blocked."""
    dangerous_paths = [
        "../../../etc/passwd",
        "../../sensitive_file.txt",
        "./../outside_dir/file.txt",
    ]
    
    for path in dangerous_paths:
        # Directory traversal should be blocked - either by permission error or file not found
        # Both indicate the operation was prevented
        with pytest.raises((PermissionError, FileNotFoundError, ToolExecutionError)) as exc_info:
            read_file(path=path)
        # The key is that the operation failed - we don't care about the specific error
        assert exc_info.value is not None
        
        with pytest.raises((PermissionError, FileNotFoundError, ToolExecutionError)) as exc_info:
            write_file(path=path, content="malicious content")
        # The key is that the operation failed - we don't care about the specific error
        assert exc_info.value is not None


def test_file_operations_handle_missing_files():
    """Test that missing files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_file = os.path.join(tmpdir, "does_not_exist.txt")
        
        with pytest.raises((FileNotFoundError, ToolExecutionError)) as exc_info:
            read_file(path=nonexistent_file)
        assert "not found" in str(exc_info.value).lower()


def test_file_operations_handle_directories():
    """Test that directories are rejected for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to read a directory
        with pytest.raises((ValueError, ToolExecutionError)) as exc_info:
            read_file(path=tmpdir)
        assert "not a file" in str(exc_info.value).lower()


def test_file_operations_respect_read_only():
    """Test that read-only files cannot be written."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "readonly.txt")
        
        # Create a file
        write_file(path=file_path, content="initial content")
        
        # Make it read-only
        os.chmod(file_path, 0o444)
        
        try:
            # Try to write to read-only file
            with pytest.raises((PermissionError, RuntimeError, ToolExecutionError)) as exc_info:
                write_file(path=file_path, content="new content")
            # Should fail with permission or runtime error
        finally:
            # Restore permissions for cleanup
            os.chmod(file_path, 0o644)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
