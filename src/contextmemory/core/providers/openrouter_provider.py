"""
OpenRouter.ai provider implementation.

OpenRouter provides a unified API for accessing multiple LLM providers.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI

from contextmemory.core.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider using OpenAI-compatible API."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            base_url: Optional custom base URL (defaults to OpenRouter API)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/samiksha0shukla/context-memory",
                "X-Title": "ContextMemory",
            },
        )
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenRouter."""
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
        """
        Create an embedding using OpenRouter.
        
        Note: OpenRouter routes to OpenAI embedding models by default.
        You can specify OpenAI models like 'openai/text-embedding-3-small'
        or use OpenRouter's model aliases.
        """
        response = self.client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding
    
    def get_default_chat_model(self) -> str:
        """Get default OpenRouter chat model (OpenAI GPT-4o-mini)."""
        return "openai/gpt-4o-mini"
    
    def get_default_embedding_model(self) -> str:
        """Get default OpenRouter embedding model (OpenAI text-embedding-3-small)."""
        return "openai/text-embedding-3-small"

