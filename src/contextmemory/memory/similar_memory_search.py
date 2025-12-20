from typing import List
from sqlalchemy.orm import Session

from src.contextmemory.db.models.memory import Memory
from src.contextmemory.memory.similarity import cosine_similarity

def search_similar_memories(db: Session, conversation_id: int, query_embeddings: List[float], limit: int=10):
    """
    Retrieve memory rows from db
    and based on cosine similarity between the retrieved memories' embeddings and candidate fact embeddings
    store top 10 most similar memory rows in scored list
    """
    
    memories = (
        db.query(Memory)
        .filter(Memory.conversation_id == conversation_id)
        .all()
    )

    scored = []
    for mem in memories:
        score = cosine_similarity(query_embeddings, mem.embedding)
        scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored[:limit]]