"""MCP tool wrapper for integrating MCP tools with terminai tool system."""

import json
import logging
from typing import Dict, Any, List, Optional

from .manager import ToolManager, ToolResult, ToolDefinition, ToolParameter
from ..mcp.client import MCPClient

logger = logging.getLogger(__name__)


class MCPToolWrapper:
    """Wrapper for integrating MCP tools with terminai tool system."""
    
    def __init__(self, mcp_client: MCPClient):
        """Initialize MCP tool wrapper."""
        self.mcp_client = mcp_client
        self.mcp_tools: Dict[str, Dict[str, Any]] = {}  # tool_name -> {server, definition}
        self.mcp_resources: Dict[str, List[Dict[str, Any]]] = {}  # server -> resources
    
    async def discover_and_register_tools(self, tool_manager: ToolManager, server_name: str):
        """Discover tools from an MCP server and register them."""
        try:
            # Get tools from the MCP server
            tools = await self.mcp_client.list_tools(server_name)
            
            for tool in tools:
                await self._register_mcp_tool(tool_manager, server_name, tool)
            
            # Also discover resources and create resource access tools
            await self._discover_and_register_resources(tool_manager, server_name)
            
            logger.info(f"Registered {len(tools)} tools from MCP server: {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to discover tools from MCP server {server_name}: {e}")
    
    async def _register_mcp_tool(self, tool_manager: ToolManager, server_name: str, tool_def: Dict[str, Any]):
        """Register a single MCP tool with the tool manager."""
        tool_name = tool_def.get("name")
        if not tool_name:
            logger.warning(f"MCP tool missing name: {tool_def}")
            return
        
        # Create a unique tool name to avoid conflicts
        unique_tool_name = f"mcp_{server_name}_{tool_name}"
        
        # Convert MCP tool schema to terminai format
        description = tool_def.get("description", f"MCP tool {tool_name} from {server_name}")
        
        # Parse input schema
        input_schema = tool_def.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Convert parameters
        parameters = {}
        for param_name, param_def in properties.items():
            parameters[param_name] = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", f"Parameter {param_name}"),
                "required": param_name in required
            }
        
        # Store MCP tool info for execution
        self.mcp_tools[unique_tool_name] = {
            "server": server_name,
            "original_name": tool_name,
            "definition": tool_def
        }
        
        # Register with tool manager
        tool_manager.register_tool(
            name=unique_tool_name,
            description=f"[MCP:{server_name}] {description}",
            parameters=parameters,
            executor=self._create_mcp_tool_executor(unique_tool_name)
        )
    
    def _create_mcp_tool_executor(self, unique_tool_name: str):
        """Create an executor function for an MCP tool."""
        async def executor(**kwargs) -> ToolResult:
            try:
                tool_info = self.mcp_tools[unique_tool_name]
                server_name = tool_info["server"]
                original_name = tool_info["original_name"]
                
                # Call the MCP tool
                result = await self.mcp_client.call_tool(server_name, original_name, kwargs)
                
                # Handle MCP response properly
                content = self._serialize_mcp_response(result)
                
                return ToolResult(
                    success=True,
                    content=content,
                    error=None
                )
                
            except Exception as e:
                logger.error(f"Error executing MCP tool {unique_tool_name}: {e}")
                return ToolResult(
                    success=False,
                    content="",
                    error=str(e)
                )
        
        return executor

    def _serialize_mcp_response(self, result: Any) -> str:
        """Serialize MCP response objects to JSON-serializable format."""
        try:
            # Handle Pydantic models
            if hasattr(result, 'model_dump'):
                # Convert Pydantic model to dict
                result_dict = result.model_dump()
                return json.dumps(result_dict, indent=2, default=str)
            
            # Handle CallToolResult specifically
            if hasattr(result, 'content') and hasattr(result, 'isError'):
                # This is likely a CallToolResult
                content_parts = []
                
                # Handle content which is a list of ContentBlock objects
                if isinstance(result.content, list):
                    for content_block in result.content:
                        if hasattr(content_block, 'model_dump'):
                            # Pydantic model
                            block_dict = content_block.model_dump()
                            if block_dict.get('type') == 'text' and 'text' in block_dict:
                                content_parts.append(block_dict['text'])
                            else:
                                content_parts.append(json.dumps(block_dict, default=str))
                        elif hasattr(content_block, 'text'):
                            # Direct text attribute
                            content_parts.append(content_block.text)
                        else:
                            content_parts.append(str(content_block))
                else:
                    # Single content
                    content_parts.append(str(result.content))
                
                return '\n'.join(content_parts)
            
            # Handle TextContent and other content types
            if hasattr(result, 'type') and hasattr(result, 'text'):
                return result.text
            
            # Handle dict-like objects
            if isinstance(result, dict):
                return json.dumps(result, indent=2, default=str)
            
            # Handle list-like objects
            if isinstance(result, list):
                serialized_items = []
                for item in result:
                    if hasattr(item, 'model_dump'):
                        serialized_items.append(item.model_dump())
                    elif hasattr(item, 'text'):
                        serialized_items.append({'text': item.text})
                    else:
                        serialized_items.append(str(item))
                return json.dumps(serialized_items, indent=2, default=str)
            
            # Fallback to string
            return str(result)
            
        except Exception as e:
            logger.error(f"Error serializing MCP response: {e}")
            return str(result)
    
    async def _discover_and_register_resources(self, tool_manager: ToolManager, server_name: str):
        """Discover resources from MCP server and create access tools."""
        try:
            resources = await self.mcp_client.list_resources(server_name)
            self.mcp_resources[server_name] = resources
            
            if resources:
                # Register a general resource access tool for this server
                tool_name = f"mcp_{server_name}_read_resource"
                
                tool_manager.register_tool(
                    name=tool_name,
                    description=f"[MCP:{server_name}] Read a resource from {server_name} MCP server",
                    parameters={
                        "uri": {
                            "type": "string",
                            "description": f"Resource URI to read from {server_name}",
                            "required": True
                        }
                    },
                    executor=self._create_resource_executor(server_name)
                )
                
                # Also register a tool to list available resources
                list_tool_name = f"mcp_{server_name}_list_resources"
                tool_manager.register_tool(
                    name=list_tool_name,
                    description=f"[MCP:{server_name}] List available resources from {server_name} MCP server",
                    parameters={},
                    executor=self._create_resource_list_executor(server_name)
                )
                
                logger.info(f"Registered resource access tools for {len(resources)} resources from {server_name}")
        
        except Exception as e:
            logger.error(f"Failed to discover resources from MCP server {server_name}: {e}")
    
    def _create_resource_executor(self, server_name: str):
        """Create an executor for reading MCP resources."""
        async def executor(uri: str) -> ToolResult:
            try:
                content = await self.mcp_client.read_resource(server_name, uri)
                return ToolResult(
                    success=True,
                    content=content,
                    error=None
                )
            except Exception as e:
                logger.error(f"Error reading resource {uri} from {server_name}: {e}")
                return ToolResult(
                    success=False,
                    content="",
                    error=str(e)
                )
        
        return executor
    
    def _create_resource_list_executor(self, server_name: str):
        """Create an executor for listing MCP resources."""
        async def executor() -> ToolResult:
            try:
                resources = self.mcp_resources.get(server_name, [])
                if not resources:
                    return ToolResult(
                        success=True,
                        content=f"No resources available from {server_name}",
                        error=None
                    )
                
                # Format resource list
                resource_list = []
                for resource in resources:
                    uri = resource.get("uri", "unknown")
                    name = resource.get("name", uri)
                    description = resource.get("description", "No description")
                    resource_list.append(f"- {name} ({uri}): {description}")
                
                content = f"Available resources from {server_name}:\n" + "\n".join(resource_list)
                
                return ToolResult(
                    success=True,
                    content=content,
                    error=None
                )
            except Exception as e:
                logger.error(f"Error listing resources from {server_name}: {e}")
                return ToolResult(
                    success=False,
                    content="",
                    error=str(e)
                )
        
        return executor
    
    def get_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered MCP tools."""
        return self.mcp_tools.copy()
    
    def get_mcp_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all discovered MCP resources."""
        return self.mcp_resources.copy()
    
    async def refresh_server_tools(self, tool_manager: ToolManager, server_name: str):
        """Refresh tools from a specific MCP server."""
        # Remove existing tools for this server
        tools_to_remove = [
            tool_name for tool_name, tool_info in self.mcp_tools.items()
            if tool_info["server"] == server_name
        ]
        
        for tool_name in tools_to_remove:
            tool_manager.unregister_tool(tool_name)
            del self.mcp_tools[tool_name]
        
        # Remove resources
        if server_name in self.mcp_resources:
            del self.mcp_resources[server_name]
        
        # Re-discover and register
        await self.discover_and_register_tools(tool_manager, server_name)
