"""
Similar Memory Search using FAISS.

This module finds memories similar to a query using vector search.
"""

from typing import List
from sqlalchemy.orm import Session

from contextmemory.db.models.memory import Memory
from contextmemory.memory.vector_store import get_vector_store, rebuild_index_from_db


def search_similar_memories(
    db: Session, 
    conversation_id: int, 
    query_embeddings: List[float], 
    limit: int = 10
) -> List[Memory]:
    """
    Find memories similar to the query embedding.
    
    Uses FAISS for O(log n) search instead of O(n) brute force.
    
    Args:
        db: Database session
        conversation_id: Conversation to search in
        query_embeddings: Query vector (1536 dimensions)
        limit: Max results to return
        
    Returns:
        List of Memory objects, ordered by similarity
    """
    # Get or create FAISS index
    vector_store = get_vector_store(conversation_id)
    
    # If index is empty, try rebuilding from DB
    if vector_store.count == 0:
        vector_store = rebuild_index_from_db(db, conversation_id)
    
    # Search FAISS (O(log n))
    results = vector_store.search(query_embeddings, k=limit)
    
    if not results:
        return []
    
    # Fetch Memory objects by IDs
    memory_ids = [r["memory_id"] for r in results]
    memories = db.query(Memory).filter(Memory.id.in_(memory_ids)).all()
    
    # Maintain similarity order
    id_to_mem = {m.id: m for m in memories}
    ordered = [id_to_mem[mid] for mid in memory_ids if mid in id_to_mem]
    
    return ordered