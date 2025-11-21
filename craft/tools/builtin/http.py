"""HTTP request tool."""

from typing import Dict, Any, Optional
from craft.tools import tool


@tool
def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Any] = None,
    auth: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Make an HTTP request with configurable options.

    Args:
        url: URL to request
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Optional HTTP headers
        body: Optional request body (will be JSON-encoded if dict)
        auth: Optional authentication dict with 'type' and credentials
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Dictionary with status_code, headers, and body

    Example:
        http_request(
            "https://api.example.com/data",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={"key": "value"},
            auth={"type": "bearer", "token": "xxx"}
        )
    """
    try:
        import httpx
    except ImportError:
        raise ImportError("httpx not installed. Install with: pip install httpx")

    headers = headers or {}
    auth_obj = None

    # Handle authentication
    if auth:
        auth_type = auth.get("type", "").lower()
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {auth.get('token')}"
        elif auth_type == "basic":
            auth_obj = (auth.get("username"), auth.get("password"))

    try:
        # Make request
        response = httpx.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            content=body if isinstance(body, (str, bytes)) else None,
            auth=auth_obj,
            timeout=timeout,
        )

        # Return response data
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
        }
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}")
