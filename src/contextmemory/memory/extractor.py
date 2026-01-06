from typing import List
from contextmemory.core.llm_client import get_llm_provider
from contextmemory.utils.extraction_system_prompt import EXTRACTION_SYSTEM_PROMPT


def extract_memories(latest_pair: List[str], summary_text: str, recent_messages: List[str]) -> List[str]:
    """
    Use LLM to extract candidate important memory facts.
    """
    provider = get_llm_provider()
    model = provider.get_default_chat_model()

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
    result = provider.chat_completion(
        model=model,
        messages=messages,
        temperature=0.1
    )
    return result["content"]