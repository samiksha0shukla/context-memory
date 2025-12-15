# from dataclasses import dataclass
# from typing import List
# from datetime import datetime
# from pydantic import BaseModel

# @dataclass
# class MemoryObj:
#     id: str
#     text: str
#     category: str
#     embedding: List[float]
#     metadata: dict
#     created_at: datetime
#     updated_at: datetime


 

# from db.database import create_table

# if __name__ == "__main__":
#     create_table()


















from sqlalchemy.orm import Session

from db.database import create_table, SessionLocal
from models.conversation import Conversation
from models.message import Message
from summary.summary_generator import generate_conversation_summary


def seed_conversation(db: Session) -> int:
    """
    Create a new conversation and return its ID
    """
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation.id


def seed_test_messages(db: Session, conversation_id: int):
    """
    Insert some fake messages for testing
    """
    messages = [
        Message(
            conversation_id=conversation_id,
            sender="user",
            message_text="Hi, I am Samiksha. I am working on an AI memory system."
        ),
        Message(
            conversation_id=conversation_id,
            sender="assistant",
            message_text="That sounds interesting. What is your goal?"
        ),
        Message(
            conversation_id=conversation_id,
            sender="user",
            message_text="I want to build a long-term memory system similar to mem0."
        ),
    ]

    db.add_all(messages)
    db.commit()


if __name__ == "__main__":
    # 1️⃣ Create tables (idempotent)
    create_table()

    # 2️⃣ Open DB session
    db: Session = SessionLocal()

    try:
        # 3️⃣ Create conversation FIRST
        conversation_id = seed_conversation(db)

        # 4️⃣ Seed messages
        seed_test_messages(db, conversation_id)

        # 5️⃣ Generate summary
        summary = generate_conversation_summary(
            db=db,
            conversation_id=conversation_id
        )

        # 6️⃣ Print result
        print("\n--- GENERATED SUMMARY ---")
        print(summary)

    finally:
        db.close()

