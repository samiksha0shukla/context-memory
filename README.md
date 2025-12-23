# ContextMemory

Long-term memory system for AI conversations.

ContextMemory extracts, stores, and retrieves important facts from conversations, enabling AI Agents to remember user preferences, context, and history across sessions.

## Installation

```bash
pip install contextmemory
```

## Quick Start

### 1. Configure

**Environment Variables**
```bash
export OPENAI_API_KEY="sk-..."
export DATABASE_URL="postgresql://..."  # Optional
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
from openai import OpenAI

# ContextMemory imports
from contextmemory import (
    configure,
    create_table,
    Memory,
    SessionLocal,
)

# CONFIGURATION

# Create DB tables
create_table()

# OpenAI client
openai_client = OpenAI()

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
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    assistant_response = response.choices[0].message.content

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
- **Flexible Storage**: SQLite (default) or PostgreSQL
- **Easy Configuration**: Programmatic or environment variable setup

## Configuration Options

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `openai_api_key` | Yes | - | Your OpenAI API key |
| `database_url` | No | `~/.contextmemory/memory.db` | Database connection URL |
| `debug` | No | `False` | Enable debug logging |

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

