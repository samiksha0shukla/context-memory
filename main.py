"""
ContextMemory Example - Interactive Chat with Memory

This example demonstrates how to use ContextMemory to build
a chatbot that remembers facts from conversations.
"""

from contextmemory import configure, Memory, create_table, SessionLocal
from contextmemory.core.openai_client import get_openai_client
from contextmemory.db.models.conversation import Conversation


def chat_with_memory(user_message: str, memory: Memory, conversation_id: int) -> str:
    """
    Generate a response using memories from past conversations.
    """
    client = get_openai_client()
    
    # Search for relevant memories
    relevant_memories = memory.search(
        query=user_message,
        conversation_id=conversation_id,
        limit=5,
    )

    # Format memories for the prompt
    memories_text = "\n".join(
        f"- {m['memory']}" for m in relevant_memories["results"]
    ) or "No memories yet."

    # Generate response with memory context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant with memory. "
                "Use the user's memories to personalize your responses.\n\n"
                f"User Memories:\n{memories_text}"
            ),
        },
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    assistant_message = response.choices[0].message.content

    # Store this conversation in memory
    memory.add(
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ],
        conversation_id=conversation_id,
    )

    return assistant_message


def main():
    """
    Main entry point - Interactive chat loop.
    """
    print("=" * 50)
    print("ContextMemory Chat Demo")
    print("=" * 50)
    print()

    # Step 1: Configure (reads from environment variables or use configure())
    # configure(openai_api_key="sk-...")  # Or set OPENAI_API_KEY env var
    
    # Step 2: Create database tables
    create_table()

    # Step 3: Create session and memory instance
    db = SessionLocal()

    try:
        # Get or create conversation
        conversation_id = input("Enter conversation ID (or press Enter for new): ").strip()
        
        if conversation_id and conversation_id.isdigit():
            conversation_id = int(conversation_id)
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                conversation = Conversation(id=conversation_id)
                db.add(conversation)
                db.commit()
                print(f"Created new conversation: {conversation_id}")
            else:
                print(f"Resuming conversation: {conversation_id}")
        else:
            conversation = Conversation()
            db.add(conversation)
            db.commit()
            conversation_id = conversation.id
            print(f"Created new conversation: {conversation_id}")

        # Initialize memory
        memory = Memory(db)

        print()
        print("Chat started! Type 'exit' to quit, 'memories' to see stored memories.")
        print("-" * 50)

        # Chat loop
        while True:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            if user_input.lower() == "memories":
                # Show all memories for this conversation
                results = memory.search(
                    query="",
                    conversation_id=conversation_id,
                    limit=20,
                )
                print("\n--- Stored Memories ---")
                for m in results["results"]:
                    print(f"  [{m['memory_id']}] {m['memory']}")
                if not results["results"]:
                    print("  No memories stored yet.")
                print("-" * 25)
                continue

            # Get AI response
            response = chat_with_memory(user_input, memory, conversation_id)
            print(f"\nAI: {response}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
