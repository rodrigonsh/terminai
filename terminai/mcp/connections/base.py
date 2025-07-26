"""Base connection interface for MCP servers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio


class BaseConnection(ABC):
    """Abstract base class for MCP server connections."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize connection with name and configuration."""
        self.name = name
        self.config = config
        self.session = None
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the MCP server."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default."""
        return self.config.get(key, default)
