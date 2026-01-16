"""
ContextMemory - Long-term memory system for AI conversations.

Configuration:
    >>> from contextmemory import configure, Memory
    
    # Using OpenAI (default)
    >>> configure(openai_api_key="sk-...")
    
    # Using OpenRouter for LLM (still needs OpenAI for embeddings)
    >>> configure(
    ...     openai_api_key="sk-...",
    ...     openrouter_api_key="sk-or-...",
    ...     llm_provider="openrouter",
    ...     llm_model="openai/gpt-4o-mini"
    ... )
    
    # Custom database
    >>> configure(openai_api_key="sk-...", database_url="postgresql://...")

Environment Variables (alternative):
    OPENAI_API_KEY - Required (for embeddings, and LLM if using OpenAI provider)
    OPENROUTER_API_KEY - Required if LLM_PROVIDER is "openrouter"
    LLM_PROVIDER - "openai" (default) or "openrouter"
    LLM_MODEL - Model name, default "gpt-4o-mini"
    EMBEDDING_MODEL - Embedding model, default "text-embedding-3-small"
    DATABASE_URL - Optional (defaults to SQLite)
"""

from contextmemory.core.settings import configure
from contextmemory.memory.memory import ContextMemory
from contextmemory.db.database import get_db, create_table, get_session_local, SessionLocal

# Alias for convenience
Memory = ContextMemory

__all__ = [
    "configure",
    "Memory", 
    "get_db", 
    "create_table", 
    "get_session_local",
    "SessionLocal",
]
