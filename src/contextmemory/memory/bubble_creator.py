"""
Bubble Creator - Creates episodic memory bubbles and finds connections.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from contextmemory.db.models.memory import Memory
from contextmemory.memory.embeddings import embed_text
from contextmemory.memory.similarity import cosine_similarity

# Configuration
CONNECTION_THRESHOLD = 0.6
MAX_CONNECTIONS = 5


def find_connections(
    db: Session,
    new_bubble: Memory,
    conversation_id: int
) -> List[int]:
    """
    Find and store connections between new bubble and existing memories.
    Returns list of connected memory IDs.
    """
    # Fetch all existing memories
    existing = db.query(Memory).filter(
        Memory.conversation_id == conversation_id,
        Memory.id != new_bubble.id,
        Memory.is_active == True
    ).all()
    
    if not existing:
        return []
    
    # Calculate similarities
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
    
    # Add reverse connections (bidirectional)
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
    
    return connection_ids


def create_bubbles(
    db: Session,
    bubbles: List[Dict],
    conversation_id: int,
    session_id: Optional[int] = None
) -> List[Memory]:
    """
    Create bubble memories and find their connections.
    
    Args:
        bubbles: [{"text": "...", "importance": 0.7}, ...]
    
    Returns:
        List of created Memory objects
    """
    created = []
    
    for bubble_data in bubbles:
        text = bubble_data.get("text", "")
        importance = bubble_data.get("importance", 0.5)
        
        if not text:
            continue
        
        # Ensure importance is a float
        if isinstance(importance, str):
            try:
                importance = float(importance)
            except ValueError:
                importance = 0.5
        
        # Generate embedding
        embedding = embed_text(text)
        
        # Create bubble record
        bubble = Memory(
            conversation_id=conversation_id,
            memory_text=text,
            embedding=embedding,
            is_episodic=True,
            occurred_at=datetime.now(timezone.utc),
            session_id=session_id,
            importance=importance,
            is_active=True,
            memory_metadata={}
        )
        
        db.add(bubble)
        db.flush()  # Get ID before finding connections
        
        # Find connections
        find_connections(db, bubble, conversation_id)
        
        created.append(bubble)
    
    db.commit()
    return created