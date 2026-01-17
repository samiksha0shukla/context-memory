import json
from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from contextmemory.db.models.memory import Memory
from contextmemory.memory.embeddings import embed_text
from contextmemory.memory.similar_memory_search import search_similar_memories
from contextmemory.memory.tool_classifier import llm_tool_call
from contextmemory.memory.vector_store import get_vector_store, save_vector_store


def update_phase(db: Session, candidate_facts: List[str], conversation_id: int):
    """
    Update phase of ContextMemory add().
    Executes LLM-selected tools and updates FAISS index.
    """
    
    vector_store = get_vector_store(conversation_id)
    
    for fact in candidate_facts:

        # Embed candidate facts
        fact_embedding = embed_text(fact)

        # Retrieve similar memories (top S = 10)
        similar_memories = search_similar_memories(
            db=db,
            conversation_id=conversation_id,
            query_embeddings=fact_embedding,
            limit=10,
        )

        # LLM decides which tool to call
        message = llm_tool_call(
            candidate_fact=fact,
            similar_memories=similar_memories,
        )

        if not message.tool_calls:
            continue
            
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Execute tool
        # ADD  
        if tool_name == "add_memory":
            memory = Memory(
                conversation_id=conversation_id,
                memory_text=args["text"],
                embedding=fact_embedding,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(memory)
            db.flush()  # Get ID before adding to FAISS
            
            # Add to FAISS index
            vector_store.add(memory.id, fact_embedding)

        # UPDATE 
        elif tool_name == "update_memory":
            memory = db.get(Memory, args["memory_id"])
            if memory:
                # Remove old from FAISS
                vector_store.remove(memory.id)
                
                memory.memory_text = args["text"]
                memory.embedding = fact_embedding
                memory.updated_at = datetime.now(timezone.utc)
                
                # Add updated to FAISS
                vector_store.add(memory.id, fact_embedding)

        # DELETE 
        elif tool_name == "delete_memory":
            memory = db.get(Memory, args["memory_id"])
            if memory:
                # Remove from FAISS
                vector_store.remove(memory.id)
                db.delete(memory)

        # NOOP
        elif tool_name == "noop":
            continue

    # Save FAISS index
    save_vector_store(conversation_id)
    
    db.commit()
