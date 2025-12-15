from datetime import datetime
from typing import List
from openai import OpenAI
from sqlalchemy.orm import Session

from models.conversation_summary import ConversationSummary
from models.message import Message

from core.openai_client import get_openai_client

#LLM Client
llm_client = get_openai_client()

#Config
SUMMARY_MODEL = "gpt-4o-mini"
MAX_MESSAGES_FROM_SUMMARY = 200

#System prompt
SUMMARY_SYSTEM_PROMPT = """
You are a conversation summarization engine.

Your job is to compress a full conversation into a factual, memory-safe summary, keeping the entire context.

Rules:
- Capture stable user facts (preferences, profile, habits)
- Keep the context 
- Capture long-term goals or constraints
- Do NOT include small talk
- Do NOT invent information
- Use neutral third-person tone
- Keep it concise but complete
"""


def generate_summary_prompt(messages: List[str]) -> List[dict]:
    """
    Builds the prompt sent to the LLM 
    """
    
    conversation_text = "\n".join(messages)

    return [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
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

    #Call llm
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