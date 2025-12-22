"""
ContextMemory - Long-term memory system for AI conversations.

Configuration:
    >>> from contextmemory import configure, Memory
    >>> configure(openai_api_key="sk-...")  # Required
    >>> configure(openai_api_key="sk-...", database_url="postgresql://...")  # Optional DB

Environment Variables (alternative):
    OPENAI_API_KEY - Required
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
