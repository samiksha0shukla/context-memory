import math
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session

from contextmemory.memory.add.add_extraction_phase import extraction_phase
from contextmemory.memory.add.add_updation_phase import update_phase

from contextmemory.memory.embeddings import embed_text
from contextmemory.db.models.memory import Memory
from contextmemory.memory.bubble_creator import create_bubbles
from contextmemory.memory.vector_store import get_vector_store, rebuild_index_from_db, save_vector_store


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
        """
        Search for relevant memories using FAISS.
        
        Args:
            query: Search query text
            conversation_id: Conversation to search
            limit: Max results
            include_connections: Include connected bubbles
            
        Returns:
            Dict with query and results
        """
        # Generate query embedding
        query_embedding = embed_text(query)
        
        # Get FAISS index
        vector_store = get_vector_store(conversation_id)
        
        # Rebuild if empty
        if vector_store.count == 0:
            vector_store = rebuild_index_from_db(self.db, conversation_id)
        
        # FAISS search (O(log n))
        faiss_results = vector_store.search(query_embedding, k=limit * 2)
        
        if not faiss_results:
            return {"query": query, "results": []}
        
        # Fetch Memory objects
        memory_ids = [r["memory_id"] for r in faiss_results]
        memories = self.db.query(Memory).filter(
            Memory.id.in_(memory_ids),
            Memory.is_active == True
        ).all()
        
        if not memories:
            return {"query": query, "results": []}
        
        # Create lookup
        id_to_mem = {m.id: m for m in memories}
        faiss_scores = {r["memory_id"]: r["score"] for r in faiss_results}
        
        # Score with recency and importance
        now = datetime.now(timezone.utc)
        scored = []
        
        for mem in memories:
            similarity = faiss_scores.get(mem.id, 0)
            
            # Recency decay for bubbles
            if mem.is_episodic and mem.occurred_at:
                # Handle timezone-naive occurred_at
                occurred = mem.occurred_at
                if occurred.tzinfo is None:
                    occurred = occurred.replace(tzinfo=timezone.utc)
                days_ago = (now - occurred).days
                recency = math.exp(-0.05 * days_ago)
            else:
                recency = 1.0
            
            importance = mem.importance if mem.importance else 0.5
            final_score = similarity * importance * recency
            scored.append((final_score, mem))
        
        # Sort and limit
        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = scored[:limit]
        
        # Collect connected bubbles
        result_ids = {mem.id for _, mem in top_results}
        connected = []
        
        if include_connections:
            for _, mem in top_results:
                if mem.memory_metadata and "connections" in mem.memory_metadata:
                    conn_ids = mem.memory_metadata["connections"].get("bubble_ids", [])
                    for conn_id in conn_ids[:2]:
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
        
        # Add connected
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
            raise ValueError(f"Memory with {memory_id} not found")
        
        # Get old embedding for removal
        conversation_id = memory.conversation_id
        
        memory.memory_text = text
        new_embedding = embed_text(text)
        memory.embedding = new_embedding
        memory.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(memory)
        
        # Update FAISS index
        vector_store = get_vector_store(conversation_id)
        vector_store.remove(memory_id)
        vector_store.add(memory_id, new_embedding)
        save_vector_store(conversation_id)

        return memory
    


    # delete()
    def delete(self, memory_id: int):
        """
        Delete a memory
        """

        memory = self.db.get(Memory, memory_id)
        if not memory: 
            raise ValueError(f"Memory with {memory_id} not found")
        
        conversation_id = memory.conversation_id
        
        # Soft delete - mark as inactive
        memory.is_active = False
        self.db.commit()
        
        # Remove from FAISS index
        vector_store = get_vector_store(conversation_id)
        vector_store.remove(memory_id)
        save_vector_store(conversation_id)

        return {"deleted_memory_id": memory_id}