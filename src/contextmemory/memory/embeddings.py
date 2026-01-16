from typing import List
from contextmemory.core.openai_client import get_embedding_client
from contextmemory.core.settings import get_settings


def embed_text(text: str) -> List[float]:
    """
    Generate the embeddings of any text.
    
    Uses the configured provider (OpenAI or OpenRouter).
    For OpenRouter, uses the openai/text-embedding-3-small model format.
    """
    settings = get_settings()
    client = get_embedding_client()
    
    # OpenRouter requires the provider prefix for embedding models
    if settings.llm_provider == "openrouter":
        model = f"openai/{settings.embedding_model}"
    else:
        model = settings.embedding_model
    
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding