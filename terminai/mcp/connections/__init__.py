"""Connection types for MCP client."""

from .base import BaseConnection
from .stdio_connection import StdioConnection
from .http_connection import HttpConnection
from .sse_connection import SSEConnection

__all__ = ["BaseConnection", "StdioConnection", "HttpConnection", "SSEConnection"]
