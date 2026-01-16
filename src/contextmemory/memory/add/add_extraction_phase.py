from typing import List
import json
from sqlalchemy.orm import Session

from contextmemory.db.models.message import Message, SenderEnum
from contextmemory.db.models.conversation_summary import ConversationSummary
from contextmemory.memory.extractor import extract_memories
from contextmemory.summary.summary_generator import generate_conversation_summary

def extraction_phase(db: Session, messages: List[dict], conversation_id: int):
    """
    Extraction phase of ContextMemory add() - extracts both semantic facts and episodic bubbles
    """

    # latest msg pair
    if len(messages) < 2:
        return []
    
    user_msg = messages[-2]
    assistant_msg = messages[-1]

    latest_pair = [
        f"{user_msg['role'].upper()}: {user_msg['content']}"
        f"{assistant_msg['role'].upper()}: {assistant_msg['content']}"
    ]

    # db extract latest summary
    summary_row = (
        db.query(ConversationSummary)
        .filter(ConversationSummary.conversation_id == conversation_id)
        .one_or_none()
    )
    summary_text = summary_row.summary_text if summary_row else ""

    # db extract 10 recent msgs
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_messages_formatted = [
        f"{msg.sender.upper()}: {msg.message_text}"
        for msg in reversed(recent_messages)
    ]

    # Call extraction agent
    extraction_result = extract_memories(
        latest_pair=latest_pair,
        summary_text=summary_text,
        recent_messages=recent_messages_formatted,
    )


    # add latest msg pair to the db
    db.add_all(
        [
            Message(
                conversation_id=conversation_id,
                sender=SenderEnum.USER,
                message_text=user_msg["content"],
            ),
            Message(
                conversation_id=conversation_id,
                sender=SenderEnum.ASSISTANT,
                message_text=assistant_msg["content"],
            ),
        ]
    )
    db.commit()

    # to check db to update summary
    generate_conversation_summary(db, conversation_id)


    # Return both types
    return {
        "semantic": extraction_result.get("semantic", []),
        "bubbles": extraction_result.get("bubbles", [])
    }