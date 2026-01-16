from typing import List, Dict
from sqlalchemy.orm import Session
from contextmemory.db.models.memory import Memory
from contextmemory.memory.similarity import cosine_similarity

CONNECTION_THRESHOLD = 0.6
MAX_CONNECTIONS = 5

def find_connections(db: Session, new_bubble: Memory, conversation_id: int) -> List[int]:
    """
    Find the connection between the new bubble and existing memories.
    Return list of connected memory IDs.
    """

    # Fetch all existing memories
    existing = db.query(Memory).filter(
        Memory.conversation_id == conversation_id,
        Memory.id != new_bubble.id,
        Memory.is_active == True
    ).all()

    if not existing:
        return []
    

    # Calculate similarity
    scored = []
    for mem in existing:
        if mem.embedding:
            score = cosine_similarity(new_bubble.embedding, mem.embedding)
            if score >= CONNECTION_THRESHOLD:
                scored.append({"id": mem.id, "score": round(score, 3)})

    
    # Sort and limit
    scored.sort(key=lambda x: x["score"], reverse=True)
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
    
    db.commit()
    return connection_ids