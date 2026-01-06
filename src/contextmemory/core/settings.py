"""
Centralized settings module for ContextMemory.

Supports two configuration methods:
1. Programmatic: configure(provider="...", api_key="...", database_url="...")
2. Environment variables: PROVIDER, API_KEY, DATABASE_URL

Supported providers: "openai", "openrouter", "gemini"
"""

from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv


@dataclass
class ContextMemorySettings:
    """Configuration settings for ContextMemory."""
    
    provider: str = "openai"  # "openai", "openrouter", or "gemini"
    api_key: Optional[str] = None
    # Legacy support - if openai_api_key is set, use it
    openai_api_key: Optional[str] = None
    database_url: Optional[str] = None
    debug: bool = False
    # Provider-specific settings
    base_url: Optional[str] = None  # For OpenRouter or custom OpenAI endpoints

    def get_database_url(self) -> str:
        """
        Return database URL or default SQLite path.
        
        If no database_url is configured, creates and returns a SQLite 
        database path at ~/.contextmemory/memory.db
        """
        if self.database_url:
            return self.database_url
        
        # Default to SQLite in user's home directory
        db_dir = os.path.expanduser("~/.contextmemory")
        os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{db_dir}/memory.db"

    def get_api_key(self) -> str:
        """Get the API key, checking both api_key and openai_api_key (legacy)."""
        if self.api_key:
            return self.api_key
        if self.openai_api_key:
            return self.openai_api_key
        return None
    
    def validate(self) -> None:
        """Validate that essential settings are present."""
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError(
                f"API key is required for provider '{self.provider}'. "
                "Either call configure(provider='...', api_key='...') or "
                "set the API_KEY environment variable in a .env file or shell."
            )
        
        if self.provider not in ["openai", "openrouter", "gemini"]:
            raise ValueError(
                f"Unknown provider: {self.provider}. "
                "Supported providers: openai, openrouter, gemini"
            )


# Global singleton for settings
_settings: Optional[ContextMemorySettings] = None


def configure(
    provider: str = "openai",
    api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,  # Legacy parameter
    database_url: Optional[str] = None,
    debug: bool = False,
    base_url: Optional[str] = None,
) -> None:
    """
    Initialize ContextMemory configuration.
    
    Args:
        provider: LLM provider to use. One of "openai", "openrouter", "gemini". Default: "openai"
        api_key: API key for the selected provider. Required unless using legacy openai_api_key.
        openai_api_key: Legacy parameter for OpenAI API key. If provided, sets provider to "openai".
        database_url: Optional. Database connection URL. 
                      If not provided, uses SQLite at ~/.contextmemory/memory.db
        debug: Optional. Enable debug mode.
        base_url: Optional. Custom base URL (useful for OpenRouter or proxies).
    
    Examples:
        >>> from contextmemory import configure
        >>> # OpenAI (default)
        >>> configure(provider="openai", api_key="sk-...")
        >>> # OpenRouter
        >>> configure(provider="openrouter", api_key="sk-or-...")
        >>> # Gemini
        >>> configure(provider="gemini", api_key="AIza...")
        >>> # Legacy OpenAI (backward compatible)
        >>> configure(openai_api_key="sk-...")
    """
    global _settings
    
    # Legacy support: if openai_api_key is provided, use it
    if openai_api_key:
        provider = "openai"
        api_key = openai_api_key
    
    _settings = ContextMemorySettings(
        provider=provider,
        api_key=api_key,
        openai_api_key=openai_api_key,  # Keep for backward compatibility
        database_url=database_url,
        debug=debug,
        base_url=base_url,
    )


def get_settings() -> ContextMemorySettings:
    """
    Get current settings.
    
    If configure() has not been called, attempts to load from environment variables.
    
    Returns:
        ContextMemorySettings instance
    """
    global _settings
    
    if _settings is None:
        # Load .env file if it exists
        load_dotenv()
        
        # Try loading from environment variables
        provider = os.environ.get("PROVIDER", "openai")
        api_key = os.environ.get("API_KEY")
        # Legacy support for OPENAI_API_KEY
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key and not api_key:
            provider = "openai"
            api_key = openai_key
        
        database_url = os.environ.get("DATABASE_URL")
        debug = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
        base_url = os.environ.get("BASE_URL")
        
        _settings = ContextMemorySettings(
            provider=provider,
            api_key=api_key,
            openai_api_key=openai_key,  # Keep for backward compatibility
            database_url=database_url,
            debug=debug,
            base_url=base_url,
        )
    
    return _settings


def reset_settings() -> None:
    """
    Reset settings to None. Useful for testing.
    """
    global _settings
    _settings = None
