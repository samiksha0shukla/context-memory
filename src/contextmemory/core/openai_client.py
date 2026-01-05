"""
OpenAI client management with lazy initialization.

This module provides backward compatibility. For new code, use get_llm_provider()
from contextmemory.core.llm_client instead.
"""

from contextmemory.core.llm_client import get_openai_client, reset_provider

# Re-export for backward compatibility
reset_client = reset_provider