import math
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session

from contextmemory.memory.add.add_extraction_phase import extraction_phase
from contextmemory.memory.add.add_updation_phase import update_phase

from contextmemory.memory.embeddings import embed_text
from contextmemory.db.models.memory import Memory
from contextmemory.memory.similarity import cosine_similarity
from contextmemory.memory.bubble_creator import create_bubbles


class ContextMemory:
    def __init__(self, db: Session):
        """
        Initialize ContextMemory with a database session.
        
        Args:
            db: SQLAlchemy Session instance
        """
        self.db = db
        


    # add()
    def add(self, messages: List[dict], conversation_id: int):
        """
        Add facts/memories to the db
        """
        
        # Extraction Phase
        extraction_result = extraction_phase(
            db=self.db,
            messages=messages,
            conversation_id=conversation_id,
        )

        semantic_facts = extraction_result.get("semantic", [])
        bubbles_data = extraction_result.get("bubbles", [])


        # Update Phase
        # Process semantic facts (existing logic)
        if semantic_facts:
            update_phase(
                db=self.db,
                candidate_facts=semantic_facts,
                conversation_id=conversation_id
            )

        # Create bubbles
        if bubbles_data:
            create_bubbles(
                db=self.db,
                bubbles=bubbles_data,
                conversation_id=conversation_id,
                session_id=None # Add session tracking later
            )
        
        return {
            "semantic": semantic_facts,
            "bubbles": [b.get("text", "") for b in bubbles_data]
        }



    # search()
    def search(self, query: str, conversation_id: int, limit: int = 10, include_connections: bool = True) -> Dict:

        # Generate query embedding
        query_embedding = embed_text(query)
        
        # Fetch all active memories
        memories = (
            self.db.query(Memory)
            .filter(
                Memory.conversation_id == conversation_id,
                Memory.is_active == True
            )
            .all()
        )
        
        if not memories:
            return {"query": query, "results": []}
        
        # Score each memory
        scored = []
        now = datetime.now(timezone.utc)
        
        for mem in memories:
            if not mem.embedding:
                continue
                
            # Similarity
            similarity = cosine_similarity(query_embedding, mem.embedding)
            
            # Recency (for bubbles only)
            if mem.is_episodic and mem.occurred_at:
                days_ago = (now - mem.occurred_at).days
                recency = math.exp(-0.05 * days_ago)
            else:
                recency = 1.0
            
            # Importance
            importance = mem.importance if mem.importance else 0.5
            
            # Final score
            final_score = similarity * importance * recency
            scored.append((final_score, mem))
        
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = scored[:limit]
        
        # Collect connected bubbles
        result_ids = {mem.id for _, mem in top_results}
        connected = []
        
        if include_connections:
            for _, mem in top_results:
                if mem.memory_metadata and "connections" in mem.memory_metadata:
                    conn_ids = mem.memory_metadata["connections"].get("bubble_ids", [])
                    for conn_id in conn_ids[:2]:  # Limit connections per memory
                        if conn_id not in result_ids:
                            conn_mem = self.db.get(Memory, conn_id)
                            if conn_mem and conn_mem.is_active:
                                connected.append(conn_mem)
                                result_ids.add(conn_id)
        
        # Format results
        results = []
        
        for score, mem in top_results:
            results.append({
                "memory_id": mem.id,
                "memory": mem.memory_text,
                "type": "bubble" if mem.is_episodic else "semantic",
                "occurred_at": mem.occurred_at.isoformat() if mem.occurred_at else None,
                "score": round(score, 4),
                "connections": (mem.memory_metadata or {}).get("connections", {}).get("bubble_ids", [])
            })
        
        # Add connected (without score)
        for conn_mem in connected[:3]:
            results.append({
                "memory_id": conn_mem.id,
                "memory": conn_mem.memory_text,
                "type": "connected",
                "occurred_at": conn_mem.occurred_at.isoformat() if conn_mem.occurred_at else None,
                "score": 0,
                "connections": []
            })
        
        return {
            "query": query,
            "total": len(results),
            "results": results
        }
        


    # update()
    def update(self, memory_id: int, text: str):
        """
        Update an existing memory
        """

        memory = self.db.get(Memory, memory_id)
        if not memory: 
            raise ValueError("Memory with {memory_id} not found")
        
        memory.memory_text = text
        memory.embedding = embed_text(text)
        memory.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(memory)

        return memory
    


    # delete()
    def delete(self, memory_id: int):
        """
        Delete a memory
        """

        memory = self.db.get(Memory, memory_id)
        if not memory: 
            raise ValueError("Memory with this {memory_id} not found")
        
        self.db.delete(memory)
        self.db.commit()

        return {"deleted_memory_id": memory_id}