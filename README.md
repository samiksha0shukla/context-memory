# ContextMemory

Long-term memory system for AI conversations - similar to Mem0/Supermemory.

ContextMemory extracts, stores, and retrieves important facts from conversations, enabling AI assistants to remember user preferences, context, and history across sessions.

## Installation

```bash
pip install contextmemory
```

## Quick Start

### 1. Configure

**Option A: Programmatic (Recommended)**
```python
from contextmemory import configure

configure(
    openai_api_key="sk-...",  # Required
    database_url="postgresql://...",  # Optional - defaults to SQLite
)
```

**Option B: Environment Variables**
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
- **PostgreSQL**: Install with `pip install contextmemory[postgres]`

## API Reference

### `configure(openai_api_key, database_url=None, debug=False)`
Initialize the library configuration.

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
