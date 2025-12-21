from datetime import datetime
from typing import List
from openai import OpenAI
from sqlalchemy.orm import Session

from src.contextmemory.db.models.conversation_summary import ConversationSummary
from src.contextmemory.db.models.message import Message

from src.contextmemory.core.openai_client import get_openai_client
from src.contextmemory.utils.summary_generator_prompt import SUMMARY_GENERATOR_PROMPT

#LLM Client
llm_client = get_openai_client()

#Config
SUMMARY_MODEL = "gpt-4o-mini"
MAX_MESSAGES_FROM_SUMMARY = 200

SUMMARY_TRIGGER_COUNT = 20


def generate_summary_prompt(messages: List[str]) -> List[dict]:
    """
    Builds the prompt sent to the LLM 
    """
    
    conversation_text = "\n".join(messages)

    return [
        {"role": "system", "content": SUMMARY_GENERATOR_PROMPT},
        {
            "role": "user",
            "content": f"""
Summarize the following conversation.

Conversation:
{conversation_text}

Return only the summary text.
"""
        }
    ] 


# Core Function
def generate_conversation_summary(db: Session, conversation_id: str) -> str:
    """
    Generates and stores a summary for a conversation.
    """

    # total count of msgs in the db
    total_count = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .count()
    )

    # Trigger condition:
    if total_count == 0 or total_count % SUMMARY_TRIGGER_COUNT != 0:
        return ""
    
    
    # Fetch all past msgs (oldest -> newest)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .limit(MAX_MESSAGES_FROM_SUMMARY)
        .all()
    )

    if not messages:
        return ""
    
    # Format msgs for LLM call 
    formatted_messages = [
        f"{msg.sender.upper()} {msg.message_text}"
        for msg in messages
    ]

    # Call llm
    prompt = generate_summary_prompt(formatted_messages)

    response = llm_client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=prompt,
        temperature=0.2
    )

    summary_text = response.choices[0].message.content.strip()

    existing_summary = (
        db.query(ConversationSummary)
        .filter(ConversationSummary.conversation_id == conversation_id)
        .one_or_none()
    )

    if existing_summary:
        existing_summary.summary_text = summary_text
        existing_summary.updated_at = datetime.utcnow()
    else:
        db.add(
            ConversationSummary(
                conversation_id=conversation_id,
                summary_text=summary_text,
                updated_at=datetime.utcnow()
            )
        )

    db.commit()

    return summary_text