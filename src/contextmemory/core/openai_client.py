"""
LLM client management with lazy initialization.

Supports multiple providers:
- openai: Direct OpenAI API
- openrouter: OpenRouter API (OpenAI-compatible)
"""

from openai import OpenAI
from contextmemory.core.settings import get_settings

# Global clients (lazy initialized)
_llm_client = None
_embedding_client = None


def get_llm_client() -> OpenAI:
    """
    Get or create the LLM client based on configured provider.
    
    Uses lazy initialization - client is created on first call.
    
    Returns:
        OpenAI-compatible client instance
        
    Raises:
        RuntimeError: If required API key is not configured
    """
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        settings.validate()
        
        if settings.llm_provider == "openrouter":
            _llm_client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/contextmemory",
                    "X-Title": "ContextMemory"
                }
            )
        else:
            _llm_client = OpenAI(api_key=settings.openai_api_key)
    
    return _llm_client


def get_embedding_client() -> OpenAI:
    """
    Get or create the embedding client based on configured provider.
    
    OpenRouter supports text-embedding-3-small, so we can use the same
    provider for embeddings.
    
    Returns:
        OpenAI-compatible client instance for embeddings
        
    Raises:
        RuntimeError: If required API key is not configured
    """
    global _embedding_client
    if _embedding_client is None:
        settings = get_settings()
        
        if settings.llm_provider == "openrouter" and settings.openrouter_api_key:
            # OpenRouter supports embeddings
            _embedding_client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/contextmemory",
                    "X-Title": "ContextMemory"
                }
            )
        elif settings.openai_api_key:
            # Fallback to OpenAI
            _embedding_client = OpenAI(api_key=settings.openai_api_key)
        else:
            raise RuntimeError(
                "API key required for embeddings. "
                "Set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable."
            )
    
    return _embedding_client


# Backward compatibility alias
def get_openai_client() -> OpenAI:
    """
    Backward compatible alias for get_llm_client().
    
    Returns:
        OpenAI-compatible client instance
    """
    return get_llm_client()


def reset_client() -> None:
    """
    Reset all clients to None. Useful for testing.
    """
    global _llm_client, _embedding_client
    _llm_client = None
    _embedding_client = None