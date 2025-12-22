from typing import List
from contextmemory.core.openai_client import get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> List[float]:
    """
    Generate the embeddings of any text.
    """
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding