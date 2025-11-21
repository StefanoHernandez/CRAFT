"""File operations tools with permission checks."""

import os
from pathlib import Path
from craft.tools import tool


@tool
def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Read file contents with permission checks.

    Args:
        path: Path to file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string

    Raises:
        PermissionError: If file cannot be read
        FileNotFoundError: If file does not exist
    """
    # Security check: prevent directory traversal (check before resolving)
    if ".." in path:
        raise PermissionError("Directory traversal not allowed")
    
    file_path = Path(path).resolve()

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check if it's a file (not directory)
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Check read permissions
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"No read permission for file: {path}")

    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read file: {e}")


@tool
def write_file(path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Write content to file with permission checks.

    Args:
        path: Path to file to write
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        True if successful

    Raises:
        PermissionError: If file cannot be written
    """
    # Security check: prevent directory traversal (check before resolving)
    if ".." in path:
        raise PermissionError("Directory traversal not allowed")
    
    file_path = Path(path).resolve()

    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Check write permissions for directory
    if not os.access(file_path.parent, os.W_OK):
        raise PermissionError(f"No write permission for directory: {file_path.parent}")

    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to write file: {e}")
