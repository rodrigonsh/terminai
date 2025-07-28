"""Base classes for LLM providers."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMMessage(BaseModel):
    """Represents a message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None


class LLMResponse(BaseModel):
    """Represents a response from the LLM."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider with configuration."""
        self.config = config
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens", 150)
        self.temperature = config.get("temperature", 0.1)
    
    @abstractmethod
    async def generate(self, messages: List[LLMMessage], tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass
    
    @abstractmethod
    def get_required_config(self) -> List[str]:
        """Get list of required configuration keys."""
        pass
    
    def format_prompt(self, prompt: str) -> List[LLMMessage]:
        """Format a prompt into messages for the LLM."""
        system_prompt = """You are a helpful AI assistant with access to tools that can help you accomplish tasks.

You have access to builtin tools and MCP (Model Context Protocol) tools from connected servers:

BUILTIN TOOLS:
- execute_command: Execute bash commands
- read_file: Read file contents
- write_to_file: Write content to files
- replace_in_file: Replace content in files
- list_files: List directory contents
- search_files: Search for files/content

MCP TOOLS:
MCP tools are prefixed with "mcp_<server>_<toolname>" and provide extended functionality from external servers.
Common MCP tools may include:
- Project management tools (create, track, manage projects)
- Database operations
- API integrations
- External service connections
- Resource access tools

When given a task, use the appropriate tools to accomplish it. Always provide clear explanations of what you're doing.

Examples:
- "list all python files" → Use list_files with pattern "*.py"
- "read the README" → Use read_file with path "README.md"
- "find files with TODO" → Use search_files with pattern "TODO"
- "create a new file" → Use write_to_file
- "test connection to takeoff" → Use mcp_takeoff_test-connection (if available)
- "find project by path" → Use mcp_takeoff_project-find-by-path (if available)

The exact MCP tools available depend on which MCP servers are connected. Use the tools that best match the user's request.
"""
        
        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=prompt)
        ]


class LLMManager:
    """Manages multiple LLM providers."""
    
    def __init__(self):
        """Initialize the LLM manager."""
        self.providers: Dict[str, type] = {}
    
    def register_provider(self, name: str, provider_class: type):
        """Register a new LLM provider."""
        self.providers[name] = provider_class
    
    def load_providers_from_config(self, config: Dict[str, Any]):
        """Load providers dynamically from configuration."""
        providers_config = config.get("llm", {}).get("providers", {})
        
        # Dynamically import and register providers based on configuration
        for name, provider_config in providers_config.items():
            provider_type = provider_config.get("type")
            if not provider_type:
                continue
                
            try:
                # Dynamically import the provider module
                module_name = f"terminai.llm.providers.{provider_type}_provider"
                class_name = f"{provider_type.capitalize()}Provider"
                
                # Import the module dynamically
                import importlib
                module = importlib.import_module(module_name)
                
                # Handle case sensitivity properly
                provider_class = None
                for attr_name in dir(module):
                    if attr_name.lower() == class_name.lower():
                        provider_class = getattr(module, attr_name)
                        break
                
                if provider_class is None:
                    raise AttributeError(f"Class {class_name} not found in {module_name}")
                
                self.register_provider(name, provider_class)
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to load provider '{name}' of type '{provider_type}': {e}")
    
    def get_provider(self, name: str, config: Dict[str, Any]) -> Optional[LLMProvider]:
        """Get an instance of a specific provider."""
        if name not in self.providers:
            return None
        
        provider_class = self.providers[name]
        return provider_class(config)
    
    def list_providers(self) -> List[str]:
        """List all available providers."""
        return list(self.providers.keys())
    
    def get_configured_providers(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Get configuration status for all providers."""
        status = {}
        for name, provider_class in self.providers.items():
            provider_config = config.get("llm", {}).get("providers", {}).get(name, {})
            try:
                provider = provider_class(provider_config)
                status[name] = provider.is_configured()
            except Exception:
                status[name] = False
        return status
