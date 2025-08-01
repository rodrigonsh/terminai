"""HTTP connection for remote MCP servers."""

import asyncio
import json
import logging
from typing import Dict, Any, List

import httpx

from .base import BaseConnection
from ..exceptions import MCPConnectionError, MCPAuthenticationError, MCPTimeoutError

logger = logging.getLogger(__name__)


class HttpConnection(BaseConnection):
    """Connection to MCP server via HTTP REST API."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get("url", "").rstrip("/")
        self.headers = config.get("headers", {})
        self.timeout = config.get("timeout", 30)
        self.client = None
    
    async def connect(self) -> bool:
        """Connect to MCP server via HTTP."""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            # Test connection by listing tools
            await self.list_tools()
            
            self.connected = True
            logger.info(f"Connected to HTTP MCP server: {self.name}")
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise MCPAuthenticationError(f"Authentication failed for {self.name}")
            else:
                raise MCPConnectionError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise MCPConnectionError(f"Connection failed for {self.name}: {e}")
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to {self.name}: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.client:
            try:
                await self.client.aclose()
            except Exception as e:
                logger.error(f"Error closing HTTP client for {self.name}: {e}")
        
        self.connected = False
        self.client = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        if not self.client:
            return []
        
        try:
            response = await self.client.get("/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list tools from {self.name}: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool."""
        if not self.client:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            response = await self.client.post(
                "/tools/call",
                json={"tool": tool_name, "arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise MCPConnectionError(f"Tool {tool_name} not found")
            else:
                raise MCPConnectionError(f"Tool call failed: {e.response.text}")
        except Exception as e:
            raise MCPConnectionError(f"Failed to call tool {tool_name}: {e}")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        if not self.client:
            return []
        
        try:
            response = await self.client.get("/resources")
            response.raise_for_status()
            return response.json().get("resources", [])
        except Exception as e:
            logger.error(f"Failed to list resources from {self.name}: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource."""
        if not self.client:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            response = await self.client.get(
                "/resources/read",
                params={"uri": uri}
            )
            response.raise_for_status()
            return response.json().get("content", "")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise MCPConnectionError(f"Resource {uri} not found")
            else:
                raise MCPConnectionError(f"Resource read failed: {e.response.text}")
        except Exception as e:
            raise MCPConnectionError(f"Failed to read resource {uri}: {e}")
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connected and self.client is not None
