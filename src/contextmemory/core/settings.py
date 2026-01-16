"""
Centralized settings module for ContextMemory.

Supports two configuration methods:
1. Programmatic: configure(openai_api_key="...", database_url="...")
2. Environment variables: OPENAI_API_KEY, DATABASE_URL

Supports multiple LLM providers:
- openai: Direct OpenAI API
- openrouter: OpenRouter API (uses OpenAI-compatible interface)
"""

from dataclasses import dataclass
from typing import Optional, Literal
import os
from dotenv import load_dotenv


LLMProvider = Literal["openai", "openrouter"]


@dataclass
class ContextMemorySettings:
    """Configuration settings for ContextMemory."""
    
    openai_api_key: Optional[str] = None
    database_url: Optional[str] = None
    debug: bool = False
    
    # LLM Provider settings
    llm_provider: LLMProvider = "openai"
    openrouter_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

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
        """Get the appropriate API key based on provider."""
        if self.llm_provider == "openrouter":
            if not self.openrouter_api_key:
                raise RuntimeError(
                    "OpenRouter API key is required when using openrouter provider. "
                    "Either call configure(openrouter_api_key='...', llm_provider='openrouter') or "
                    "set the OPENROUTER_API_KEY environment variable."
                )
            return self.openrouter_api_key
        else:
            if not self.openai_api_key:
                raise RuntimeError(
                    "OpenAI API key is required. "
                    "Either call configure(openai_api_key='...') or "
                    "set the OPENAI_API_KEY environment variable."
                )
            return self.openai_api_key
    
    def get_base_url(self) -> Optional[str]:
        """Get the base URL for the LLM provider."""
        if self.llm_provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        return None  # OpenAI uses default

    def validate(self) -> None:
        """Validate that essential settings are present."""
        # Validate based on provider
        if self.llm_provider == "openrouter":
            if not self.openrouter_api_key:
                raise RuntimeError(
                    "OpenRouter API key is required when using openrouter provider. "
                    "Either call configure(openrouter_api_key='...', llm_provider='openrouter') or "
                    "set the OPENROUTER_API_KEY environment variable."
                )
            # OpenRouter supports embeddings, so OpenAI key is optional
        else:
            if not self.openai_api_key:
                raise RuntimeError(
                    "OpenAI API key is required. "
                    "Either call configure(openai_api_key='...') or "
                    "set the OPENAI_API_KEY environment variable in a .env file or shell."
                )


# Global singleton for settings
_settings: Optional[ContextMemorySettings] = None


def configure(
    openai_api_key: Optional[str] = None,
    database_url: Optional[str] = None,
    debug: bool = False,
    llm_provider: LLMProvider = "openai",
    openrouter_api_key: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
) -> None:
    """
    Initialize ContextMemory configuration.
    
    Args:
        openai_api_key: Required for OpenAI provider, also needed for embeddings with OpenRouter.
        database_url: Optional. Database connection URL. 
                      If not provided, uses SQLite at ~/.contextmemory/memory.db
        debug: Optional. Enable debug mode.
        llm_provider: LLM provider to use. Options: "openai", "openrouter"
        openrouter_api_key: Required when llm_provider is "openrouter".
        llm_model: Model to use for LLM calls. Default: "gpt-4o-mini"
        embedding_model: Model to use for embeddings. Default: "text-embedding-3-small"
    
    Example:
        >>> from contextmemory import configure
        
        # Using OpenAI directly
        >>> configure(openai_api_key="sk-...")
        
        # Using OpenRouter (still needs OpenAI key for embeddings)
        >>> configure(
        ...     openai_api_key="sk-...",
        ...     openrouter_api_key="sk-or-...",
        ...     llm_provider="openrouter",
        ...     llm_model="openai/gpt-4o-mini"
        ... )
    """
    global _settings
    _settings = ContextMemorySettings(
        openai_api_key=openai_api_key,
        database_url=database_url,
        debug=debug,
        llm_provider=llm_provider,
        openrouter_api_key=openrouter_api_key,
        llm_model=llm_model,
        embedding_model=embedding_model,
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
        openai_key = os.environ.get("OPENAI_API_KEY")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        database_url = os.environ.get("DATABASE_URL")
        debug = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
        
        # Determine provider from env
        llm_provider = os.environ.get("LLM_PROVIDER", "openai")
        if llm_provider not in ("openai", "openrouter"):
            llm_provider = "openai"
        
        llm_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        
        _settings = ContextMemorySettings(
            openai_api_key=openai_key,
            database_url=database_url,
            debug=debug,
            llm_provider=llm_provider,
            openrouter_api_key=openrouter_key,
            llm_model=llm_model,
            embedding_model=embedding_model,
        )
    
    return _settings


def reset_settings() -> None:
    """
    Reset settings to None. Useful for testing.
    """
    global _settings
    _settings = None
