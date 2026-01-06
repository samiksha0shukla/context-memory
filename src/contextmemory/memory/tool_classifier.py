from typing import List
from contextmemory.core.llm_client import get_llm_provider
from contextmemory.utils.tool_call_system_prompt import TOOL_CALL_SYSTEM_PROMPT

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
    that is, decides what to do with this candidate fact.
    """
    provider = get_llm_provider()
    model = provider.get_default_chat_model()
    
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

    result = provider.chat_completion(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )

    # Return OpenAI-compatible message object
    class Message:
        def __init__(self, result: dict):
            self.content = result.get("content")
            tool_calls = result.get("tool_calls", [])
            if tool_calls:
                self.tool_calls = [self.ToolCall(tc) for tc in tool_calls]
            else:
                self.tool_calls = None
        
        class ToolCall:
            def __init__(self, tc: dict):
                self.id = tc.get("id")
                self.type = tc.get("type")
                self.function = self.Function(tc.get("function", {}))
            
            class Function:
                def __init__(self, func: dict):
                    self.name = func.get("name")
                    self.arguments = func.get("arguments")
    
    return Message(result)