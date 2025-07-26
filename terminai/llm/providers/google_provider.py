"""Google provider implementation."""

import os
import google.generativeai as genai
from typing import Dict, Any, List

from ..base import LLMProvider, LLMMessage, LLMResponse


class GoogleProvider(LLMProvider):
    """Google LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Google provider."""
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        self.model_instance = None
        
        if self.is_configured():
            genai.configure(api_key=self.api_key)
            self.model_instance = genai.GenerativeModel(self.model)
    
    async def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Generate response using Google API."""
        if not self.model_instance:
            raise RuntimeError("Google client not initialized. Please check your API key.")
            
        try:
            # Convert messages to Google format
            conversation = []
            system_prompt = None
            
            for msg in messages:
                if msg.role == "system":
                    system_prompt = msg.content
                else:
                    conversation.append(f"{msg.role}: {msg.content}")
            
            prompt = "\n".join(conversation)
            if system_prompt:
                prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await self.model_instance.generate_content_async(
                prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            )
            
            return LLMResponse(
                content=response.text.strip(),
                model=self.model
            )
        except Exception as e:
            raise RuntimeError(f"Google API error: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if Google provider is configured."""
        return bool(self.api_key)
    
    def get_required_config(self) -> List[str]:
        """Get required configuration for Google."""
        return ["api_key"]
