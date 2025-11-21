"""Built-in tools for CRAFT agents."""

from craft.tools.builtin.web_search import duckduckgo_search, google_search
from craft.tools.builtin.calculator import calculate
from craft.tools.builtin.database import query_database
from craft.tools.builtin.http import http_request
from craft.tools.builtin.files import read_file, write_file
from craft.tools.builtin.email import send_email

__all__ = [
    "duckduckgo_search",
    "google_search",
    "calculate",
    "query_database",
    "http_request",
    "read_file",
    "write_file",
    "send_email",
]
