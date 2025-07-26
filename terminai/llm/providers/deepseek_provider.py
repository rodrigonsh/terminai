"""DeepSeek provider implementation."""

import os
import json
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

from ..base import LLMProvider, LLMMessage, LLMResponse


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider using OpenAI-compatible API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize DeepSeek provider."""
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = config.get("base_url", "https://api.deepseek.com/v1")
        self.client = None
        
        if self.is_configured():
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                
            self.client = AsyncOpenAI(**client_kwargs)
    
    async def generate(self, messages: List[LLMMessage], tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """Generate response using DeepSeek API."""
        if not self.client:
            raise RuntimeError("DeepSeek client not initialized. Please check your API key.")
            
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_msg = {"role": msg.role, "content": msg.content}
                if msg.tool_call_id:
                    openai_msg["tool_call_id"] = msg.tool_call_id
                openai_messages.append(openai_msg)
            
            # Prepare API call
            api_kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            if tools:
                api_kwargs["tools"] = tools
                api_kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**api_kwargs)
            
            # Extract tool calls if present
            tool_calls = None
            if response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    }
                    for call in response.choices[0].message.tool_calls
                ]
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                tool_calls=tool_calls,
                usage=response.usage.dict() if response.usage else None,
                model=response.model
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if DeepSeek provider is configured."""
        return bool(self.api_key)
    
    def get_required_config(self) -> List[str]:
        """Get required configuration for DeepSeek."""
        return ["api_key"]
