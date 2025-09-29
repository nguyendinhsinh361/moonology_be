"""
Memory management service.
"""

from typing import Dict

from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage

from app.repositories.chat_session import ChatSessionRepository

# In-memory cache for conversation memories
_memory_cache: Dict[str, ConversationBufferMemory] = {}


def get_memory(session_id: str) -> ConversationBufferMemory:
    """
    Get or create a conversation memory for a session.

    Args:
        session_id (str): The session ID

    Returns:
        ConversationBufferMemory: A conversation memory instance
    """
    global _memory_cache

    if session_id in _memory_cache:
        return _memory_cache[session_id]

    # Create a new memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Load previous messages from the database
    repo = ChatSessionRepository()
    messages = repo.get_session_messages(session_id)

    # Populate memory with previous messages
    for msg in messages:
        if msg["role"] == "user":
            memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            memory.chat_memory.add_message(AIMessage(content=msg["content"]))

    _memory_cache[session_id] = memory
    return memory


def save_message_to_memory(session_id: str, role: str, content: str) -> None:
    """
    Save a message to both the memory and the database.

    Args:
        session_id (str): The session ID
        role (str): The message role (user or assistant)
        content (str): The message content
    """
    # Get the memory for this session
    memory = get_memory(session_id)

    # Add message to memory
    if role == "user":
        memory.chat_memory.add_message(HumanMessage(content=content))
    elif role == "assistant":
        memory.chat_memory.add_message(AIMessage(content=content))

    # Save to database
    repo = ChatSessionRepository()
    repo.add_message_to_session(session_id, role, content)


def clear_memory(session_id: str) -> None:
    """
    Clear the memory for a session.

    Args:
        session_id (str): The session ID
    """
    global _memory_cache

    if session_id in _memory_cache:
        del _memory_cache[session_id]
