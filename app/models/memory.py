import time
import uuid
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_mongodb import MongoDBChatMessageHistory

from app.core.config import settings
from app.models.vector_store import get_vector_store


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


class VectorChatMessageHistory(BaseChatMessageHistory):
    """
    A chat message history that uses vector search to retrieve relevant messages.
    """

    def __init__(
        self,
        session_id: str,
        namespace: str = "chat_messages",
        k: int = 10,
        score_threshold: float = 0.6,
    ):
        """
        Initialize the vector chat message history.

        Args:
            session_id (str): A unique identifier for the conversation
            namespace (str): Namespace in Pinecone
            k (int): Number of relevant messages to retrieve
            score_threshold (float): Minimum similarity score (0.0 to 1.0) for vector search
        """
        self.session_id = session_id
        self.namespace = namespace
        self.k = k
        self.score_threshold = score_threshold
        self.mongodb_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGODB_URI,
            database_name=settings.MONGODB_DB_NAME,
            collection_name="chat_history",
            session_id=session_id,
        )
        self.vector_store = get_vector_store(collection_name=namespace)
        self._current_query = None

    def set_current_query(self, query: str):
        """
        Set the current query for retrieving relevant messages.

        Args:
            query (str): The current user query
        """
        self._current_query = query

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get the relevant messages from the chat history.

        Returns:
            List[BaseMessage]: The relevant messages based on the current query
        """
        # If we don't have a query, just return the recent messages
        if not self._current_query:
            return self.mongodb_history.messages[
                -5:
            ]  # Return the 5 most recent messages for context

        # Get relevant messages from vector store
        relevant_messages = self.vector_store.search_similar_messages(
            query=self._current_query,
            session_id=self.session_id,
            k=self.k,
            score_threshold=self.score_threshold,
        )

        # Add the 3 most recent messages for conversational continuity
        recent_messages = (
            self.mongodb_history.messages[-3:] if self.mongodb_history.messages else []
        )

        # Combine and deduplicate messages (we prefer recent messages if there's a duplicate)
        seen_contents = {msg.content for msg in recent_messages}
        deduplicated_messages = list(recent_messages)

        for msg in relevant_messages:
            if msg.content not in seen_contents:
                deduplicated_messages.append(msg)
                seen_contents.add(msg.content)

        return deduplicated_messages

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to the chat history.

        Args:
            message (BaseMessage): The message to add
        """
        # Add to MongoDB
        self.mongodb_history.add_message(message)

        # Add to vector store with metadata
        metadata = {"timestamp": int(time.time()), "message_id": str(uuid.uuid4())}
        self.vector_store.add_message(message, self.session_id, metadata)

    def clear(self) -> None:
        """
        Clear the conversation history.
        Note: This only clears MongoDB history, not the vector store.
        To clear the vector store, a new collection/namespace should be created.
        """
        # We can't easily clear specific documents from Pinecone based on session ID
        # So we only clear MongoDB history
        if hasattr(self.mongodb_history, "clear"):
            self.mongodb_history.clear()


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
) -> VectorChatMessageHistory:
    """
    Create a vector-based chat history that retrieves relevant messages.

    Args:
        session_id (str): A unique identifier for the conversation
        k (int): Number of relevant messages to retrieve
        score_threshold (float): Minimum similarity score (0.0 to 1.0) for vector search

    Returns:
        VectorChatMessageHistory: A chat history that uses vector search
    """
    return VectorChatMessageHistory(session_id=session_id, k=k, score_threshold=score_threshold)


def get_conversation_memory(
    session_id,
    memory_key="chat_history",
    return_messages=True,
    max_messages=10,
    use_vector=True,
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
        use_vector (bool): Whether to use vector-based retrieval
        score_threshold (float): Minimum similarity score (0.0 to 1.0) for vector search
        role_filter (str, optional): Filter messages by role (e.g., "user", "ai")

    Returns:
        BaseChatMessageHistory: A history object to use in chains
    """
    # In newer versions of LangChain, we use ChatMessageHistory directly
    # instead of ConversationBufferMemory
    if use_vector:
        return get_vector_chat_history(session_id, k=max_messages, score_threshold=score_threshold)
    else:
        return get_mongodb_chat_history(
            session_id, max_messages=max_messages, role_filter=role_filter
        )
