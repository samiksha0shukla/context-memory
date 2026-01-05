"""
LLM Provider abstraction layer.

Supports multiple providers:
- OpenAI (default)
- OpenRouter.ai
- Google Gemini
"""

from contextmemory.core.providers.base import BaseProvider
from contextmemory.core.providers.openai_provider import OpenAIProvider
from contextmemory.core.providers.openrouter_provider import OpenRouterProvider
from contextmemory.core.providers.gemini_provider import GeminiProvider

__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "GeminiProvider",
    "get_provider",
]


def get_provider(provider_name: str, **kwargs) -> BaseProvider:
    """
    Factory function to get a provider instance.
    
    Args:
        provider_name: One of "openai", "openrouter", "gemini"
        **kwargs: Provider-specific configuration (api_key, base_url, etc.)
    
    Returns:
        BaseProvider instance
    
    Raises:
        ValueError: If provider_name is not supported
    """
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_name == "openrouter":
        return OpenRouterProvider(**kwargs)
    elif provider_name == "gemini":
        return GeminiProvider(**kwargs)
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported providers: openai, openrouter, gemini"
        )

