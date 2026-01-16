import json
from typing import List, Dict, Any
from contextmemory.core.openai_client import get_llm_client
from contextmemory.core.settings import get_settings
from contextmemory.utils.extraction_system_prompt import EXTRACTION_SYSTEM_PROMPT


def extract_memories(latest_pair: List[str], summary_text: str, recent_messages: List[str]) -> Dict[str, Any]:
    """
    Use LLM to extract candidate memory facts (semantic facts and bubbles).
    
    Returns:
        {
            "semantic": ["fact1", "fact2"],
            "bubbles": [{"text": "...", "importance": 0.7}]
        }
    """
    settings = get_settings()
    llm_client = get_llm_client()

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

Extract memory facts (semantic facts and bubbles).
"""
        }
    ]

    # Get model from settings (supports OpenRouter format like "openai/gpt-4o-mini")
    model = settings.llm_model

    # LLM extracts memory facts 
    response = llm_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1
    )

    raw_output = response.choices[0].message.content
    
    
    # Parse JSON
    try:
        result = json.loads(raw_output)
        # Validate structure
        if "semantic" not in result:
            result["semantic"] = []
        if "bubbles" not in result:
            result["bubbles"] = []
        return result
    except json.JSONDecodeError:
        return {"semantic": [], "bubbles": []}