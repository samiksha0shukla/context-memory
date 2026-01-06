"""
OpenAI provider implementation.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI

from contextmemory.core.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI provider using the official OpenAI SDK."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional custom base URL (for proxies, etc.)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenAI."""
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        
        response = self.client.chat.completions.create(**kwargs)
        
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
        }
        
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]
        
        return result
    
    def create_embedding(
        self,
        model: str,
        text: str,
    ) -> List[float]:
        """Create an embedding using OpenAI."""
        response = self.client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding
    
    def get_default_chat_model(self) -> str:
        """Get default OpenAI chat model."""
        return "gpt-4o-mini"
    
    def get_default_embedding_model(self) -> str:
        """Get default OpenAI embedding model."""
        return "text-embedding-3-small"

