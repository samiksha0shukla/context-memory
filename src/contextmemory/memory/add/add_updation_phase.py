import json
from typing import List
from datetime import datetime 
from sqlalchemy.orm import Session

from src.contextmemory.db.models.memory import Memory
from src.contextmemory.memory.embeddings import embed_text
from src.contextmemory.memory.similar_memory_search import search_similar_memories
from src.contextmemory.memory.tool_classifier import llm_tool_call

def update_phase(db: Session, candidate_facts: List[str], conversation_id: int):
    """
    Update phase of ContextMemory add().
    Executes LLM-selected tools.
    """
    
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
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(memory)

        # UPDATE 
        elif tool_name == "update_memory":
            memory = db.get(Memory, args["memory_id"])
            if memory:
                memory.memory_text = args["text"]
                memory.embedding=fact_embedding
                memory.updated_at=datetime.utcnow()

        # DELETE 
        elif tool_name == "delete_memory":
            memory = db.get(Memory, args["memory_id"])
            if memory:
                db.delete(memory)

        # NOOP
        elif tool_name == "noop":
            continue

    db.commit()