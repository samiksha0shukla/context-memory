"""
Centralized settings module for ContextMemory.

Supports two configuration methods:
1. Programmatic: configure(openai_api_key="...", database_url="...")
2. Environment variables: OPENAI_API_KEY, DATABASE_URL
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ContextMemorySettings:
    """Configuration settings for ContextMemory."""
    
    openai_api_key: Optional[str] = None
    database_url: Optional[str] = None
    debug: bool = False

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

    def validate(self) -> None:
        """Validate that required settings are present."""
        if not self.openai_api_key:
            raise RuntimeError(
                "OpenAI API key is required. "
                "Either call configure(openai_api_key='...') or "
                "set the OPENAI_API_KEY environment variable."
            )


# Global singleton for settings
_settings: Optional[ContextMemorySettings] = None


def configure(
    openai_api_key: str,
    database_url: Optional[str] = None,
    debug: bool = False,
) -> None:
    """
    Initialize ContextMemory configuration.
    
    Args:
        openai_api_key: Required. Your OpenAI API key.
        database_url: Optional. Database connection URL. 
                      If not provided, uses SQLite at ~/.contextmemory/memory.db
        debug: Optional. Enable debug mode.
    
    Example:
        >>> from contextmemory import configure
        >>> configure(openai_api_key="sk-...")
        >>> configure(openai_api_key="sk-...", database_url="postgresql://...")
    """
    global _settings
    _settings = ContextMemorySettings(
        openai_api_key=openai_api_key,
        database_url=database_url,
        debug=debug,
    )


def get_settings() -> ContextMemorySettings:
    """
    Get current settings.
    
    If configure() has not been called, attempts to load from environment variables.
    Raises RuntimeError if OpenAI API key is not available.
    
    Returns:
        ContextMemorySettings instance
        
    Raises:
        RuntimeError: If OpenAI API key is not configured
    """
    global _settings
    
    if _settings is None:
        # Try loading from environment variables
        openai_key = os.environ.get("OPENAI_API_KEY")
        database_url = os.environ.get("DATABASE_URL")
        debug = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
        
        _settings = ContextMemorySettings(
            openai_api_key=openai_key,
            database_url=database_url,
            debug=debug,
        )
    
    # Validate before returning
    _settings.validate()
    return _settings


def reset_settings() -> None:
    """
    Reset settings to None. Useful for testing.
    """
    global _settings
    _settings = None
