"""
Base provider interface for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers must implement:
    - chat_completion: For text generation
    - create_embedding: For text embeddings
    """
    
    @abstractmethod
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion.
        
        Args:
            model: Model name/identifier
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            tools: Optional list of function/tool definitions
            tool_choice: Optional tool choice strategy ("auto", "none", etc.)
        
        Returns:
            Dict with 'content' (str) and optionally 'tool_calls' (list)
        """
        pass
    
    @abstractmethod
    def create_embedding(
        self,
        model: str,
        text: str,
    ) -> List[float]:
        """
        Create an embedding for text.
        
        Args:
            model: Embedding model name/identifier
            text: Text to embed
        
        Returns:
            List of float values representing the embedding
        """
        pass
    
    @abstractmethod
    def get_default_chat_model(self) -> str:
        """Get the default chat model for this provider."""
        pass
    
    @abstractmethod
    def get_default_embedding_model(self) -> str:
        """Get the default embedding model for this provider."""
        pass

