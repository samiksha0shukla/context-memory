"""
Update Phase - Processes semantic facts using LLM-decided actions.
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from contextmemory.core.settings import get_settings
from contextmemory.db.models.memory import Memory
from contextmemory.memory.embeddings import embed_text
from contextmemory.memory.similar_memory_search import search_similar_memories
from contextmemory.memory.tool_classifier import llm_tool_call
from contextmemory.memory.vector_store import get_vector_store, save_vector_store


def update_phase(db: Session, candidate_facts: List[str], conversation_id: int):
    """
    Update phase of ContextMemory add().
    Executes LLM-selected actions and updates FAISS index.
    """
    settings = get_settings()
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

        if settings.debug:
            print(f"[DEBUG] Similar memories found: {len(similar_memories)}")
            for m in similar_memories[:3]:
                print(f"  - ID {m.id}: {m.memory_text[:50]}...")

        # LLM decides which action to take
        decision = llm_tool_call(
            candidate_fact=fact,
            similar_memories=similar_memories,
        )

        if settings.debug:
            print(f"[DEBUG] Decision: {decision.action} for fact: {fact[:50]}...")

        # Execute action
        if decision.action == "ADD":
            text_to_store = decision.text or fact
            memory = Memory(
                conversation_id=conversation_id,
                memory_text=text_to_store,
                embedding=fact_embedding,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(memory)
            db.flush()  # Get ID before adding to FAISS

            # Add to FAISS index
            vector_store.add(memory.id, fact_embedding)

            if settings.debug:
                print(f"[DEBUG] Added memory ID {memory.id}")

        elif decision.action == "UPDATE" and decision.memory_id:
            memory = db.get(Memory, decision.memory_id)
            if memory:
                # Remove old from FAISS
                vector_store.remove(memory.id)

                memory.memory_text = decision.text or fact
                memory.embedding = fact_embedding
                memory.updated_at = datetime.now(timezone.utc)

                # Add updated to FAISS
                vector_store.add(memory.id, fact_embedding)

                if settings.debug:
                    print(f"[DEBUG] Updated memory ID {memory.id}")

        elif decision.action == "DELETE" and decision.memory_id:
            memory = db.get(Memory, decision.memory_id)
            if memory:
                # Remove from FAISS
                vector_store.remove(memory.id)
                # Soft delete - consistent with Memory.delete()
                memory.is_active = False

                if settings.debug:
                    print(f"[DEBUG] Soft-deleted memory ID {decision.memory_id}")

        elif decision.action == "REPLACE" and decision.memory_id:
            # REPLACE = soft-delete old contradictory memory + ADD new one
            old_memory = db.get(Memory, decision.memory_id)
            if old_memory:
                # Remove old from FAISS and soft-delete from DB
                vector_store.remove(old_memory.id)
                old_memory.is_active = False

                if settings.debug:
                    print(f"[DEBUG] Soft-deleted contradictory memory ID {old_memory.id}")

            # Add the new fact
            text_to_store = decision.text or fact
            new_memory = Memory(
                conversation_id=conversation_id,
                memory_text=text_to_store,
                embedding=fact_embedding,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_memory)
            db.flush()

            # Add to FAISS index
            vector_store.add(new_memory.id, fact_embedding)

            if settings.debug:
                print(
                    f"[DEBUG] Added replacement memory ID {new_memory.id}: {text_to_store[:50]}..."
                )

        elif decision.action == "NOOP":
            if settings.debug:
                print("[DEBUG] NOOP - fact already exists or not worth storing")

    # Save FAISS index
    save_vector_store(conversation_id)

    db.commit()
