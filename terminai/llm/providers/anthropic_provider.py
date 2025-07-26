"""Anthropic provider implementation."""

import os
from typing import Dict, Any, List
from anthropic import AsyncAnthropic

from ..base import LLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider."""
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = config.get("base_url")
        self.client = None
        
        if self.is_configured():
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                
            self.client = AsyncAnthropic(**client_kwargs)
    
    async def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Generate response using Anthropic API."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized. Please check your API key.")
            
        try:
            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_message
            )
            
            return LLMResponse(
                content=response.content[0].text.strip(),
                usage=response.usage.dict() if response.usage else None,
                model=response.model
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if Anthropic provider is configured."""
        return bool(self.api_key)
    
    def get_required_config(self) -> List[str]:
        """Get required configuration for Anthropic."""
        return ["api_key"]
