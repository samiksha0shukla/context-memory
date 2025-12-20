from typing import List
from src.contextmemory.core.openai_client import get_openai_client
from src.contextmemory.utils.tool_call_system_prompt import TOOL_CALL_SYSTEM_PROMPT

client = get_openai_client()

MODEL_NAME = "gpt-4o-mini"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_memory",
            "description": "Add a new memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": "Update an existing memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "integer"},
                    "text": {"type": "string"}
                },
                "required": ["memory_id", "text"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_memory",
            "description": "Delete an existing memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "integer"}
                },
                "required": ["memory_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "noop",
            "description": "Do nothing",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def llm_tool_call(candidate_fact: str, similar_memories: List):
    """
    LLM decides which TOOL to call
    by taking one candidate fact and 10 similar memories 
    that is, decides what to do with this candidate fact
    """
    
    memory_context = "\n".join(
        f"-ID {m.id}: {m.memory_text}" for m in similar_memories
    )

    messages = [
        {"role": "system", "content": TOOL_CALL_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
Candidate fact:
{candidate_fact}

Similar existing memories:
{memory_context}
"""
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )

    return response.choices[0].message