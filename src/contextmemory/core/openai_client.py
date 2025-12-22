"""
OpenAI client management with lazy initialization.
"""

from openai import OpenAI
from contextmemory.core.settings import get_settings

# Global client (lazy initialized)
_client = None


def get_openai_client() -> OpenAI:
    """
    Get or create the OpenAI client.
    
    Uses lazy initialization - client is created on first call.
    
    Returns:
        OpenAI client instance
        
    Raises:
        RuntimeError: If OpenAI API key is not configured
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def reset_client() -> None:
    """
    Reset client to None. Useful for testing.
    """
    global _client
    _client = None