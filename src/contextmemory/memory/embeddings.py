from typing import List
from contextmemory.core.llm_client import get_llm_provider


def embed_text(text: str) -> List[float]:
    """
    Generate the embeddings of any text.
    """
    provider = get_llm_provider()
    model = provider.get_default_embedding_model()
    
    return provider.create_embedding(model=model, text=text)