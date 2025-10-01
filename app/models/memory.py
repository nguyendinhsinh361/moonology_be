import time
import uuid
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_mongodb import MongoDBChatMessageHistory

from app.core.config import settings


class LimitedMongoDBChatMessageHistory(MongoDBChatMessageHistory):
    """
    A MongoDB-backed chat message history that only retrieves the most recent messages.
    """

    def __init__(
        self,
        connection_string,
        database_name,
        collection_name,
        session_id,
        max_messages=10,
        role_filter=None,
    ):
        """
        Initialize the limited MongoDB chat message history.

        Args:
            connection_string (str): The MongoDB connection string
            database_name (str): The name of the MongoDB database
            collection_name (str): The name of the MongoDB collection
            session_id (str): A unique identifier for the conversation
            max_messages (int): Maximum number of messages to retrieve
            role_filter (str, optional): Filter messages by role (e.g., "user", "ai")
        """
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            collection_name=collection_name,
            session_id=session_id,
        )
        self.max_messages = max_messages
        self.role_filter = role_filter

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get the most recent messages from the chat history.

        Returns:
            List[BaseMessage]: The most recent messages (limited to max_messages)
        """
        # Call the parent method to get all messages
        all_messages = super().messages

        # Filter by role if specified
        if self.role_filter and all_messages:
            filtered_messages = [msg for msg in all_messages if msg.type == self.role_filter]
            return filtered_messages[-self.max_messages :] if filtered_messages else []

        # Return only the most recent messages, limited by max_messages
        return all_messages[-self.max_messages :] if all_messages else []




def get_mongodb_chat_history(session_id, max_messages=10, role_filter=None):
    """
    Create a MongoDB-backed chat message history with a limit on retrieved messages.

    Args:
        session_id (str): A unique identifier for the conversation
        max_messages (int): Maximum number of messages to retrieve
        role_filter (str, optional): Filter messages by role (e.g., "user", "ai")

    Returns:
        LimitedMongoDBChatMessageHistory: A chat history stored in MongoDB with limited retrieval
    """
    return LimitedMongoDBChatMessageHistory(
        connection_string=settings.MONGODB_URI,
        database_name=settings.MONGODB_DB_NAME,
        collection_name="chat_history",
        session_id=session_id,
        max_messages=max_messages,
        role_filter=role_filter,
    )


def get_vector_chat_history(
    session_id: str, k: int = 10, score_threshold: float = 0.6
) -> LimitedMongoDBChatMessageHistory:
    """
    Create a chat history (now just MongoDB-based, no vector search).

    Args:
        session_id (str): A unique identifier for the conversation
        k (int): Number of relevant messages to retrieve (ignored, uses max_messages)
        score_threshold (float): Minimum similarity score (ignored)

    Returns:
        LimitedMongoDBChatMessageHistory: A chat history using MongoDB only
    """
    return get_mongodb_chat_history(session_id, max_messages=k)


def get_conversation_memory(
    session_id,
    memory_key="chat_history",
    return_messages=True,
    max_messages=10,
    use_vector=False,  # Disabled - no vector store
    score_threshold=0.6,
    role_filter=None,
):
    """
    Create a conversation memory with MongoDB backend.

    Args:
        session_id (str): A unique identifier for the conversation
        memory_key (str): The key to use for the memory in the chain
        return_messages (bool): Whether to return the history as messages
        max_messages (int): Maximum number of messages to retrieve
        use_vector (bool): Whether to use vector-based retrieval (disabled)
        score_threshold (float): Minimum similarity score (ignored)
        role_filter (str, optional): Filter messages by role (e.g., "user", "ai")

    Returns:
        BaseChatMessageHistory: A history object to use in chains
    """
    # Always use MongoDB history since vector store is disabled
    return get_mongodb_chat_history(
        session_id, max_messages=max_messages, role_filter=role_filter
    )
