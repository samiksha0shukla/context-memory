# ContextMemory

Long-term memory system for AI conversations.

ContextMemory extracts, stores, and retrieves important facts from conversations, enabling AI Agents to remember user preferences, context, and history across sessions.

## Installation

```bash
pip install contextmemory
```

## Quick Start

### 1. Configure

ContextMemory supports multiple LLM providers:
- **OpenAI** (default) - Requires `openai` package
- **OpenRouter.ai** - Unified API for multiple models, requires `openai` package
- **Google Gemini** - Requires `google-generativeai` package (install with `pip install contextmemory[gemini]`)

**Environment Variables**
```bash
# OpenAI (default)
export PROVIDER="openai"
export API_KEY="sk-..."  # or use OPENAI_API_KEY for backward compatibility

# OpenRouter.ai
export PROVIDER="openrouter"
export API_KEY="sk-or-..."

# Google Gemini
export PROVIDER="gemini"
export API_KEY="AIza..."

# Optional
export DATABASE_URL="postgresql://..."
export BASE_URL="https://..."  # Custom base URL (for OpenRouter or proxies)
```

**Programmatic Configuration**
```python
from contextmemory import configure

# OpenAI (default)
configure(provider="openai", api_key="sk-...")

# OpenRouter.ai
configure(provider="openrouter", api_key="sk-or-...")

# Google Gemini
configure(provider="gemini", api_key="AIza...")

# Legacy OpenAI (still supported)
configure(openai_api_key="sk-...")  # Automatically uses OpenAI provider
```

### 2. Initialize Database

```python
from contextmemory import create_table

create_table()  # Creates all required tables
```

### 3. Use Memory System

```python
from contextmemory import Memory, SessionLocal

# Create session and memory instance
db = SessionLocal()
memory = Memory(db)

# Add memories from a conversation
messages = [
    {"role": "user", "content": "Hi, I'm John and I love Python programming"},
    {"role": "assistant", "content": "Nice to meet you John! Python is great."},
]
memory.add(messages=messages, conversation_id=1)

# Search memories
results = memory.search(
    query="What programming language does the user like?",
    conversation_id=1,
    limit=5
)
print(results)
# {'query': '...', 'results': [{'memory_id': 1, 'memory': 'User loves Python programming', 'score': 0.89}]}

# Update a memory
memory.update(memory_id=1, text="User is an expert Python developer")

# Delete a memory
memory.delete(memory_id=1)
```

## Demonstration Code:

```python
from contextmemory.core.llm_client import get_llm_provider

# ContextMemory imports
from contextmemory import (
    configure,
    create_table,
    Memory,
    SessionLocal,
)

# CONFIGURATION

# Configure provider (OpenAI, OpenRouter, or Gemini)
configure(provider="openai", api_key="sk-...")  # or use environment variables

# Create DB tables
create_table()

# Get LLM provider client
llm_provider = get_llm_provider()

# Database session + memory
db = SessionLocal()
memory = Memory(db)


# CHAT FUNCTION
def chat_with_memories(
    message: str,
    conversation_id: int = 1,
) -> str:
    """
    Chat with AI using ContextMemory for long-term memory.
    """

    # 1. Retrieve relevant memories
    search_results = memory.search(
        query=message,
        conversation_id=conversation_id,
        limit=3,
    )

    memories_str = "\n".join(
        f"- {entry['memory']}"
        for entry in search_results["results"]
    )

    # 2. Build prompt
    system_prompt = (
        "You are a helpful AI. Answer the user's question using the provided memories.\n\n"
        f"User Memories:\n{memories_str}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    # 3. Call LLM
    result = llm_provider.chat_completion(
        model=llm_provider.get_default_chat_model(),
        messages=messages,
    )

    assistant_response = result["content"]

    # 4. Store memories from conversation
    messages.append(
        {"role": "assistant", "content": assistant_response}
    )

    memory.add(
        messages=messages,
        conversation_id=conversation_id,
    )

    return assistant_response


# CLI LOOP
def main():
    print("Chat with AI using ContextMemory (type 'exit' to quit)")

    conversation_id = 19  # fixed for testing

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        reply = chat_with_memories(
            user_input,
            conversation_id=conversation_id,
        )
        print(f"AI: {reply}")


if __name__ == "__main__":
    main()
```

## Features

- **Automatic Memory Extraction**: Uses LLM to extract important facts from conversations
- **Semantic Search**: Find relevant memories using embedding-based similarity
- **Memory Deduplication**: Automatically updates or removes duplicate memories
- **Multi-Provider Support**: Works with OpenAI, OpenRouter.ai, and Google Gemini
- **Flexible Storage**: SQLite (default) or PostgreSQL
- **Easy Configuration**: Programmatic or environment variable setup

## Configuration Options

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `provider` | No | `"openai"` | LLM provider: `"openai"`, `"openrouter"`, or `"gemini"` |
| `api_key` | Yes* | - | API key for the selected provider |
| `openai_api_key` | Yes* | - | Legacy: OpenAI API key (sets provider to "openai") |
| `database_url` | No | `~/.contextmemory/memory.db` | Database connection URL |
| `base_url` | No | - | Custom base URL (useful for OpenRouter or proxies) |
| `debug` | No | `False` | Enable debug logging |

\* Either `api_key` or `openai_api_key` is required.

### Provider-Specific Notes

**OpenAI**
- Default models: `gpt-4o-mini` (chat), `text-embedding-3-small` (embeddings)
- No additional packages required

**OpenRouter.ai**
- Default models: `openai/gpt-4o-mini` (chat), `openai/text-embedding-3-small` (embeddings)
- Supports any model available on OpenRouter
- No additional packages required (uses OpenAI SDK)
- Example: `configure(provider="openrouter", api_key="sk-or-...", base_url="https://openrouter.ai/api/v1")`

**Google Gemini**
- Default models: `gemini-1.5-flash` (chat), `models/text-embedding-004` (embeddings)
- Requires: `pip install contextmemory[gemini]` or `pip install google-generativeai`
- Example: `configure(provider="gemini", api_key="AIza...")`

## Database Support

- **SQLite** (default): No additional setup required

## API Reference

### `Memory(db: Session)`
Main memory interface class.

#### Methods:
- `add(messages: List[dict], conversation_id: int)` - Extract and store memories
- `search(query: str, conversation_id: int, limit: int)` - Search memories
- `update(memory_id: int, text: str)` - Update a memory
- `delete(memory_id: int)` - Delete a memory

### `create_table()`
Create all required database tables.

### `SessionLocal()`
Get a new database session.

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Links

- [GitHub Repository](https://github.com/samiksha0shukla/context-memory)
- [Issue Tracker](https://github.com/samiksha0shukla/context-memory/issues)

