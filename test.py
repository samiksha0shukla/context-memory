# version:1 for sqlalchemy and db
# from db.database import create_table

# if __name__ == "__main__":
#     create_table()

















# version:2 for summary generator
# from sqlalchemy.orm import Session

# from db.database import create_table, SessionLocal
# from models.conversation import Conversation
# from models.message import Message
# from summary.summary_generator import generate_conversation_summary


# def seed_conversation(db: Session) -> int:
#     """
#     Create a new conversation and return its ID
#     """
#     conversation = Conversation()
#     db.add(conversation)
#     db.commit()
#     db.refresh(conversation)
#     return conversation.id


# def seed_test_messages(db: Session, conversation_id: int):
#     """
#     Insert some fake messages for testing
#     """
#     messages = [
#         Message(
#             conversation_id=conversation_id,
#             sender="user",
#             message_text="Hi, I am Samiksha. I am working on an AI memory system."
#         ),
#         Message(
#             conversation_id=conversation_id,
#             sender="assistant",
#             message_text="That sounds interesting. What is your goal?"
#         ),
#         Message(
#             conversation_id=conversation_id,
#             sender="user",
#             message_text="I want to build a long-term memory system similar to supermemory."
#         ),
#     ]

#     db.add_all(messages)
#     db.commit()


# if __name__ == "__main__":
#     # 1️⃣ Create tables (idempotent)
#     create_table()

#     # 2️⃣ Open DB session
#     db: Session = SessionLocal()

#     try:
#         # 3️⃣ Create conversation FIRST
#         conversation_id = seed_conversation(db)

#         # 4️⃣ Seed messages
#         seed_test_messages(db, conversation_id)

#         # 5️⃣ Generate summary
#         summary = generate_conversation_summary(
#             db=db,
#             conversation_id=conversation_id
#         )

#         # 6️⃣ Print result
#         print("\n--- GENERATED SUMMARY ---")
#         print(summary)

#     finally:
#         db.close()

























# from sqlalchemy.orm import Session

# from db.database import create_table, SessionLocal
# from models.conversation import Conversation
# from models.message import Message
# from models.memory import Memory  # your memory ORM model
# from contextmemory.memory import ContextMemory


# def seed_conversation(db: Session) -> int:
#     """Create a conversation and return its ID"""
#     conversation = Conversation()
#     db.add(conversation)
#     db.commit()
#     db.refresh(conversation)
#     return conversation.id


# def insert_message(
#     db: Session,
#     conversation_id: int,
#     sender: str,
#     text: str,
# ):
#     """Insert a single message into DB"""
#     msg = Message(
#         conversation_id=conversation_id,
#         sender=sender,
#         message_text=text,
#     )
#     db.add(msg)
#     db.commit()


# if __name__ == "__main__":
#     # 1️⃣ Create DB tables
#     create_table()

#     # 2️⃣ Open DB session
#     db: Session = SessionLocal()

#     try:
#         # 3️⃣ Create conversation
#         conversation_id = seed_conversation(db)
#         print(f"\nConversation created with ID: {conversation_id}")

#         # 4️⃣ Create memory system
#         memory_system = ContextMemory(db)

#         # 5️⃣ Simulate chat turns
#         messages = []

#         # ---- Turn 1 ----
#         user_msg = "Hi, I am Samiksha. I am working on an AI memory system."
#         assistant_msg = "That sounds interesting. What is your goal?"

#         insert_message(db, conversation_id, "user", user_msg)
#         insert_message(db, conversation_id, "assistant", assistant_msg)

#         messages.append({"role": "user", "content": user_msg})
#         messages.append({"role": "assistant", "content": assistant_msg})

#         extracted = memory_system.add(
#             messages=messages,
#             conversation_id=conversation_id,
#         )

#         print("\nExtracted facts after turn 1:")
#         print(extracted)

#         # ---- Turn 2 ----
#         user_msg = "I want to build a long-term memory system similar to supermemory."
#         assistant_msg = "Nice, long-term memory is a hard but valuable problem."

#         insert_message(db, conversation_id, "user", user_msg)
#         insert_message(db, conversation_id, "assistant", assistant_msg)

#         messages.append({"role": "user", "content": user_msg})
#         messages.append({"role": "assistant", "content": assistant_msg})

#         extracted = memory_system.add(
#             messages=messages,
#             conversation_id=conversation_id,
#         )

#         print("\nExtracted facts after turn 2:")
#         print(extracted)

#         # 6️⃣ Inspect stored memories
#         print("\n--- STORED MEMORIES IN DB ---")
#         stored_memories = (
#             db.query(Memory)
#             .filter(Memory.conversation_id == conversation_id)
#             .all()
#         )

#         for mem in stored_memories:
#             print(f"- {mem.memory_text}")

#     finally:
#         db.close()




























# for testing add and search method: 
from src.contextmemory.core.openai_client import get_openai_client
from sqlalchemy.orm import Session

from src.contextmemory.db.database import create_table, SessionLocal
from src.contextmemory.db.models.conversation import Conversation
from src.contextmemory.memory.memory import ContextMemory

openai_client = get_openai_client()


def chat_with_memories(
    message: str,
    memory: ContextMemory,
    conversation_id: int,
) -> str:
    # Retrieve relevant memories
    relevant_memories = memory.search(
        query=message,
        conversation_id=conversation_id,
        limit=3,
    )

    memories_str = "\n".join(
        f"- {entry['memory']}"
        for entry in relevant_memories["results"]
    )

    # Generate Assistant response
    system_prompt = (
        "You are a helpful AI. Answer the question based on query and memories.\n"
        f"User Memories:\n{memories_str}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=messages,
    )

    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation
    messages.append(
        {"role": "assistant", "content": assistant_response}
    )

    memory.add(
        messages=messages,
        conversation_id=conversation_id,
    )

    return assistant_response


def main():
    print("Chat with AI (type 'exit' to quit)")

    # 1️⃣ Create tables
    create_table()

    # 2️⃣ Open DB session
    db: Session = SessionLocal()

    try:
        # 3️⃣ Create conversation
        conversation = Conversation()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        conversation_id = conversation.id

        # 4️⃣ Initialize memory system
        memory = ContextMemory(db)

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            print(
                f"AI: {chat_with_memories(user_input, memory, conversation_id)}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()






























# test for delete and update methods 
# from sqlalchemy.orm import Session

# from db.database import SessionLocal
# from contextmemory.memory import ContextMemory


# # 🔹 Lightweight client wrapper (Mem0-style)
# class MemoryClient:
#     def __init__(self, db: Session):
#         self.memory = ContextMemory(db)

#     def update(self, memory_id: int, text: str):
#         return self.memory.update(
#             memory_id=memory_id,
#             text=text,
#         )

#     def delete(self, memory_id: int):
#         return self.memory.delete(memory_id=memory_id)


# if __name__ == "__main__":
#     # 1️⃣ Open DB session
#     db: Session = SessionLocal()

#     try:
#         # 2️⃣ Create client
#         client = MemoryClient(db)

#         # ---------- TEST UPDATE ----------
#         print("\n--- TESTING UPDATE ---")

#         memory_id = 11
#         updated = client.update(
#             memory_id=memory_id,
#             text="User is vegetarian",
#         )

#         print("Updated Memory:")
#         print(f"ID: {updated.id}")
#         print(f"Text: {updated.memory_text}")

#         # ---------- TEST DELETE ----------
#         print("\n--- TESTING DELETE ---")

#         memory_id = 3
#         result = client.delete(memory_id=memory_id)

#         print(result)

#     finally:
#         db.close()
