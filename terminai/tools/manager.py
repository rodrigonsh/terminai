"""Tool manager for handling tool registration and execution."""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """Represents a tool parameter."""
    type: str
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    """Represents a tool definition."""
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Represents the result of a tool execution."""
    success: bool
    content: str
    error: Optional[str] = None


class ToolManager:
    """Manages tool registration and execution."""
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.executors: Dict[str, Callable[..., Awaitable[ToolResult]]] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Dict[str, Any]],
        executor: Callable[..., Awaitable[ToolResult]]
    ):
        """Register a new tool."""
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters={
                param_name: ToolParameter(**param_def)
                for param_name, param_def in parameters.items()
            },
            required=[name for name, param in parameters.items() if param.get("required", True)]
        )
        
        self.tools[name] = tool_def
        self.executors[name] = executor
        logger.info(f"Registered tool: {name}")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for LLM consumption."""
        definitions = []
        for tool_def in self.tools.values():
            definition = {
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": tool_def.required
                    }
                }
            }
            
            for param_name, param in tool_def.parameters.items():
                definition["function"]["parameters"]["properties"][param_name] = {
                    "type": param.type,
                    "description": param.description
                }
            
            definitions.append(definition)
        
        return definitions
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given arguments."""
        if name not in self.tools:
            return ToolResult(
                success=False,
                content="",
                error=f"Tool '{name}' not found"
            )
        
        if name not in self.executors:
            return ToolResult(
                success=False,
                content="",
                error=f"No executor found for tool '{name}'"
            )
        
        try:
            # Validate required parameters
            tool_def = self.tools[name]
            missing_params = [
                param for param in tool_def.required
                if param not in arguments
            ]
            
            if missing_params:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Missing required parameters: {', '.join(missing_params)}"
                )
            
            # Execute the tool
            result = await self.executors[name](**arguments)
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self.tools.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if name not in self.tools:
            return None
        
        tool_def = self.tools[name]
        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": {
                name: {
                    "type": param.type,
                    "description": param.description,
                    "required": name in tool_def.required
                }
                for name, param in tool_def.parameters.items()
            }
        }
