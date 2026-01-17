"""
Connection Finder - Finds connections between bubbles using FAISS.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
from contextmemory.db.models.memory import Memory
from contextmemory.memory.vector_store import get_vector_store

CONNECTION_THRESHOLD = 0.6
MAX_CONNECTIONS = 5


def find_connections(db: Session, new_bubble: Memory, conversation_id: int) -> List[int]:
    """
    Find the connection between the new bubble and existing memories using FAISS.
    Return list of connected memory IDs.
    
    Uses FAISS for fast similarity search instead of O(n) loop.
    """
    if not new_bubble.embedding:
        return []
    
    # Use FAISS to find similar memories (O(log n))
    vector_store = get_vector_store(conversation_id)
    
    # Search for more than we need to filter by threshold
    results = vector_store.search(new_bubble.embedding, k=MAX_CONNECTIONS * 2)
    
    if not results:
        return []
    
    # Filter by threshold and exclude self
    scored = []
    for r in results:
        if r["memory_id"] != new_bubble.id and r["score"] >= CONNECTION_THRESHOLD:
            scored.append({"id": r["memory_id"], "score": round(r["score"], 3)})
    
    top_connections = scored[:MAX_CONNECTIONS]
    
    if not top_connections:
        return []
    
    # Store in new bubble's metadata
    connection_ids = [c["id"] for c in top_connections]
    connection_scores = {str(c["id"]): c["score"] for c in top_connections}
    metadata = new_bubble.memory_metadata or {}
    metadata["connections"] = {
        "bubble_ids": connection_ids,
        "scores": connection_scores
    }
    new_bubble.memory_metadata = metadata

    # Add reverse connection (bidirectional)
    for conn in top_connections:
        connected_mem = db.get(Memory, conn["id"])
        if connected_mem:
            cm_metadata = connected_mem.memory_metadata or {}
            cm_connections = cm_metadata.get("connections", {"bubble_ids": [], "scores": {}})
            
            if new_bubble.id not in cm_connections["bubble_ids"]:
                cm_connections["bubble_ids"].append(new_bubble.id)
                cm_connections["scores"][str(new_bubble.id)] = conn["score"]
                cm_metadata["connections"] = cm_connections
                connected_mem.memory_metadata = cm_metadata
    
    # Note: Don't commit here - let caller handle commit
    return connection_ids