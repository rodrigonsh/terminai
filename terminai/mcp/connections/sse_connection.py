"""SSE connection for remote MCP servers using Server-Sent Events."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp import types

from .base import BaseConnection
from ..exceptions import MCPConnectionError, MCPAuthenticationError

logger = logging.getLogger(__name__)


class SSEConnection(BaseConnection):
    """Connection to MCP server via Server-Sent Events using MCP SDK."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get("url", "").rstrip("/")
        self.headers = config.get("headers", {})
        self.timeout = config.get("timeout", 30)
        self._session_context = None
        self._session_task = None
    
    async def connect(self) -> bool:
        """Connect to MCP server via SSE using MCP SDK."""
        try:
            logger.info(f"Connecting to MCP SSE server: {self.name} at {self.base_url}")
            logger.info(f"Headers: {self.headers}")
            
            # Start the session context manager in a background task
            self._session_task = asyncio.create_task(self._run_session())
            
            # Wait a bit for the connection to establish
            await asyncio.sleep(2)
            
            if self.connected:
                logger.info(f"Successfully connected to MCP SSE server: {self.name}")
                return True
            else:
                raise MCPConnectionError("Connection failed to establish")
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP SSE server {self.name}: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                raise MCPAuthenticationError(f"Authentication failed for {self.name}")
            else:
                raise MCPConnectionError(f"Connection failed for {self.name}: {e}")
    
    async def _run_session(self):
        """Run the MCP session following the official SDK pattern."""
        try:
            logger.info(f"Starting SSE client for {self.name}")
            
            # Use the MCP SDK's SSE client following the official pattern
            async with sse_client(
                url=self.base_url,
                headers=self.headers,
                timeout=self.timeout,
                sse_read_timeout=300  # 5 minutes
            ) as (read_stream, write_stream):
                
                logger.info(f"SSE client context established for {self.name}")
                
                # Create and run the MCP client session
                async with ClientSession(
                    read_stream=read_stream,
                    write_stream=write_stream,
                    client_info=types.Implementation(
                        name="terminai",
                        version="1.0.0"
                    )
                ) as session:
                    
                    logger.info(f"ClientSession created for {self.name}, initializing...")
                    
                    # Initialize the MCP session
                    await session.initialize()
                    
                    # Store the session and mark as connected
                    self._session_context = session
                    self.connected = True
                    logger.info(f"MCP SSE connection established and initialized for {self.name}")
                    
                    # Keep the session alive until cancelled
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        logger.info(f"Session task cancelled for {self.name}")
                        raise
                        
        except asyncio.CancelledError:
            logger.info(f"Session cancelled for {self.name}")
            raise
        except Exception as e:
            logger.error(f"Session error for {self.name}: {e}")
            logger.exception(f"Full traceback for {self.name}:")
            raise
        finally:
            # Clean up
            self.connected = False
            self._session_context = None
            logger.info(f"Session ended for {self.name}")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            if self._session_task:
                self._session_task.cancel()
                try:
                    await self._session_task
                except asyncio.CancelledError:
                    pass
                self._session_task = None
            
            self.connected = False
            self._session_context = None
            logger.info(f"Disconnected from MCP SSE server: {self.name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools using MCP protocol."""
        if not self._session_context:
            logger.warning(f"No session available for {self.name}")
            return []
        
        try:
            result = await self._session_context.list_tools()
            tools = []
            if hasattr(result, 'tools'):
                for tool in result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description if hasattr(tool, 'description') else "",
                        "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                    })
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools from {self.name}: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool using MCP protocol."""
        if not self._session_context:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            result = await self._session_context.call_tool(tool_name, arguments)
            return {
                "content": result.content if hasattr(result, 'content') else [],
                "isError": result.isError if hasattr(result, 'isError') else False
            }
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.name}: {e}")
            raise MCPConnectionError(f"Failed to call tool {tool_name}: {e}")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources using MCP protocol."""
        if not self._session_context:
            return []
        
        try:
            result = await self._session_context.list_resources()
            resources = []
            if hasattr(result, 'resources'):
                for resource in result.resources:
                    resources.append({
                        "uri": resource.uri if hasattr(resource, 'uri') else "",
                        "name": resource.name if hasattr(resource, 'name') else "",
                        "description": resource.description if hasattr(resource, 'description') else "",
                        "mimeType": resource.mimeType if hasattr(resource, 'mimeType') else ""
                    })
            return resources
        except Exception as e:
            logger.error(f"Failed to list resources from {self.name}: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource using MCP protocol."""
        if not self._session_context:
            raise MCPConnectionError(f"Server {self.name} not connected")
        
        try:
            result = await self._session_context.read_resource(uri)
            # Combine all content parts into a single string
            content_parts = []
            if hasattr(result, 'contents'):
                for content in result.contents:
                    if hasattr(content, 'text'):
                        content_parts.append(content.text)
                    elif hasattr(content, 'data'):
                        content_parts.append(str(content.data))
            return "\n".join(content_parts)
        except Exception as e:
            logger.error(f"Failed to read resource {uri} from {self.name}: {e}")
            raise MCPConnectionError(f"Failed to read resource {uri}: {e}")
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connected and self._session_context is not None
