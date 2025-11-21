"""Database query tool with SQL injection prevention."""

from typing import List, Dict, Any, Optional
from craft.tools import tool


@tool
def query_database(
    sql: str, params: Optional[Dict[str, Any]] = None, connection_string: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Execute a parameterized SQL query safely.

    Uses parameterized queries to prevent SQL injection attacks.
    Supports SQLite, PostgreSQL, and MySQL.

    Args:
        sql: SQL query with parameter placeholders (use :param_name or ?)
        params: Dictionary of parameters for the query
        connection_string: Database connection string (optional, can use env var DB_CONNECTION_STRING)

    Returns:
        List of rows as dictionaries

    Example:
        query_database(
            "SELECT * FROM users WHERE age > :min_age",
            params={"min_age": 18}
        )
    """
    import os

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        raise ImportError("sqlalchemy not installed. Install with: pip install sqlalchemy")

    # Get connection string
    conn_str = connection_string or os.getenv("DB_CONNECTION_STRING")
    if not conn_str:
        raise ValueError(
            "Database connection string required. "
            "Set DB_CONNECTION_STRING environment variable or pass as argument."
        )

    params = params or {}

    try:
        # Create engine and execute query
        engine = create_engine(conn_str)
        with engine.connect() as connection:
            result = connection.execute(text(sql), params)

            # Convert to list of dicts
            rows = []
            for row in result:
                rows.append(dict(row._mapping))

            return rows
    except Exception as e:
        raise RuntimeError(f"Database query failed: {e}")
