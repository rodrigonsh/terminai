"""MCP client for terminai."""

import asyncio
import json
from typing import Dict, Any, List, Optional
import logging

from .connections import BaseConnection, StdioConnection, HttpConnection, SSEConnection
from .exceptions import MCPConnectionError, MCPConfigurationError

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self):
        """Initialize MCP client."""
        self.connections: Dict[str, BaseConnection] = {}
        self.server_configs: List[Dict[str, Any]] = []
    
    def _create_connection(self, name: str, config: Dict[str, Any]) -> BaseConnection:
        """Create appropriate connection based on configuration."""
        connection_type = config.get("type", "stdio")
        
        if connection_type == "stdio":
            return StdioConnection(name, config)
        elif connection_type == "http":
            return HttpConnection(name, config)
        elif connection_type == "sse":
            return SSEConnection(name, config)
        else:
            raise MCPConfigurationError(f"Unknown connection type: {connection_type}")
    
    async def connect_server(self, name: str, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server."""
        try:
            connection = self._create_connection(name, config)
            success = await connection.connect()
            if success:
                self.connections[name] = connection
                logger.info(f"Connected to MCP server: {name}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools from an MCP server."""
        if server_name not in self.connections:
            return []
        
        connection = self.connections[server_name]
        return await connection.list_tools()
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server."""
        if server_name not in self.connections:
            raise ValueError(f"Server {server_name} not connected")
        
        connection = self.connections[server_name]
        return await connection.call_tool(tool_name, arguments)
    
    async def list_resources(self, server_name: str) -> List[Dict[str, Any]]:
        """List available resources from an MCP server."""
        if server_name not in self.connections:
            return []
        
        connection = self.connections[server_name]
        return await connection.list_resources()
    
    async def read_resource(self, server_name: str, uri: str) -> str:
        """Read a resource from an MCP server."""
        if server_name not in self.connections:
            raise ValueError(f"Server {server_name} not connected")
        
        connection = self.connections[server_name]
        return await connection.read_resource(uri)
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected MCP servers."""
        return [name for name, conn in self.connections.items() if conn.is_connected()]
    
    async def disconnect_server(self, name: str) -> None:
        """Disconnect from an MCP server."""
        if name in self.connections:
            try:
                await self.connections[name].disconnect()
                del self.connections[name]
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")
    
    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for name in list(self.connections.keys()):
            await self.disconnect_server(name)
    
    def get_connection_info(self, server_name: str) -> Dict[str, Any]:
        """Get connection information for a server."""
        if server_name not in self.connections:
            return {}
        
        connection = self.connections[server_name]
        return {
            "name": server_name,
            "type": connection.config.get("type", "stdio"),
            "connected": connection.is_connected(),
            "config": connection.config
        }
