"""Stdio connection for local MCP servers."""

import asyncio
import logging
from typing import Dict, Any, List

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

from .base import BaseConnection
from ..exceptions import MCPConnectionError

logger = logging.getLogger(__name__)


class StdioConnection(BaseConnection):
    """Connection to MCP server via stdio (local process)."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._session = None
        self._stdio_context = None
    
    async def connect(self) -> bool:
        """Connect to MCP server via stdio."""
        if not MCP_AVAILABLE:
            raise MCPConnectionError("MCP not available")
        
        try:
            server_params = StdioServerParameters(
                command=self.get_config_value("command"),
                args=self.get_config_value("args", []),
                env=self.get_config_value("env", {})
            )
            
            self._stdio_context = stdio_client(server_params)
            read, write = await self._stdio_context.__aenter__()
            
            self._session = ClientSession(read, write)
            await self._session.initialize()
            
            self.connected = True
            logger.info(f"Connected to stdio MCP server: {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to stdio MCP server {self.name}: {e}")
            raise MCPConnectionError(f"Failed to connect to {self.name}: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"Error closing session for {self.name}: {e}")
        
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing stdio context for {self.name}: {e}")
        
        self.connected = False
        self._session = None
        self._stdio_context = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        if not self._session:
            return []
        
        try:
            tools = await self._session.list_tools()
            return [tool.dict() for tool in tools]
        except Exception as e:
            logger.error(f"Failed to list tools from {self.name}: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool."""
        if not self._session:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            result = await self._session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.name}: {e}")
            raise
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        if not self._session:
            return []
        
        try:
            resources = await self._session.list_resources()
            return [resource.dict() for resource in resources]
        except Exception as e:
            logger.error(f"Failed to list resources from {self.name}: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource."""
        if not self._session:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            content = await self._session.read_resource(uri)
            return content
        except Exception as e:
            logger.error(f"Failed to read resource {uri} from {self.name}: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connected and self._session is not None
