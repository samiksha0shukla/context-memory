from typing import List
from src.contextmemory.core.openai_client import get_openai_client
from src.contextmemory.utils.extraction_system_prompt import EXTRACTION_SYSTEM_PROMPT

llm_client = get_openai_client()

EXTRACTION_MODEL = "gpt-4o-mini"


def extract_memories(latest_pair: List[str], summary_text: str, recent_messages: List[str]) -> List[str]:
    """
    Use LLM to extract candidate important memory facts
    """

    # List of string -> Single string
    recent_msgs_text = "\n".join(recent_messages)
    latest_pair_text = "\n".join(latest_pair)

    # Format msgs to give to LLM for extraction
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user", 
            "content" : f"""
Conversation Summary:
{summary_text}

Recent Messages:
{recent_msgs_text}

Latest Interaction:
{latest_pair_text}

Extract memory facts.
"""
        }
    ]

    # LLM extracts memory facts 
    response = llm_client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=messages,
        temperature=0.1
    )
    return response.choices[0].message.content