from typing import List, Dict
from sqlalchemy.orm import Session
from src.contextmemory.db.database import SessionLocal

from src.contextmemory.memory.add.add_extraction_phase import extraction_phase
from src.contextmemory.memory.add.add_updation_phase import update_phase

from src.contextmemory.memory.embeddings import embed_text
from src.contextmemory.db.models.memory import Memory
from src.contextmemory.memory.similarity import cosine_similarity

from datetime import datetime


class ContextMemory:
    def __init__(self, db: Session | None = None):
        self.db = db or SessionLocal()
        


    # add()
    def add(self, messages: List[dict], conversation_id: int):
        """
        Add facts/memories to the db
        """
        
        # Extraction Phase
        candidate_facts = extraction_phase(
            db=self.db,
            messages=messages,
            conversation_id=conversation_id,
        )

        if not candidate_facts:
            return[]


        # Update Phase
        update_phase(
            db=self.db,
            candidate_facts=candidate_facts,
            conversation_id=conversation_id,
        )
        
        return candidate_facts



    # search()
    def search(self, query: str, conversation_id: int, limit: int) -> Dict:
        """
        Search the similar memories as per user's query
        """

        # query embedding
        query_embedding = embed_text(query)

        # memory object extraction from db
        memories = (
            self.db.query(Memory)
            .filter(Memory.conversation_id == conversation_id)
            .all()
        )

        if not memories:
            return {
                "query": query,
                "results": [],
            }

        # similarity score of each memory 
        scored_memories = []
        for mem in memories:
            score = cosine_similarity(query_embedding, mem.embedding)
            scored_memories.append((score, mem))

        # sort by similarity score (descending)
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        # take top-k as per "limit" 
        top_memories = scored_memories[:limit]

        # format response
        results = [
            {
                "memory_id": mem.id,
                "memory": mem.memory_text,
                "score": round(score, 4),
            }
            for score, mem in top_memories
        ]

        return {
            "query": query,
            "results": results,
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
        memory.updated_at = datetime.utcnow()

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