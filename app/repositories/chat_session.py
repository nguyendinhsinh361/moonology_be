"""
Chat session repository module.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.constants import DEFAULT_MODEL_PROVIDER
from app.enum.model import ModelGeminiName, ModelOpenAiName, ModelProvider
from app.repositories.mongodb import MongoRepository


class ChatSessionRepository(MongoRepository):
    """Repository for chat sessions."""

    def __init__(self):
        """Initialize the chat session repository."""
        super().__init__("chat_sessions")

    def create_session(
        self,
        model_provider: ModelProvider = ModelProvider.GEMINI,
        model_name: str = None,
        model_params: Dict[str, Any] = None,
        card_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new chat session.

        Args:
            model_provider (ModelProvider): The LLM provider to use
            model_name (str, optional): The specific model name
            model_params (Dict[str, Any], optional): Additional model parameters
            card_ids (Optional[List[str]], optional): List of card IDs associated with this session
        Returns:
            str: The session ID
        """

        session_id = str(uuid.uuid4())

        # Store the string value of the enum in MongoDB
        provider_value = (
            model_provider.value
            if isinstance(model_provider, ModelProvider)
            else str(model_provider)
        )

        # Set default model name based on provider if not provided
        if model_name is None or model_name == "":
            if provider_value == ModelProvider.OPENAI.value:
                model_name = ModelOpenAiName.OPENAI_GPT_4_1_NANO.value
            else:  # Default to Gemini
                model_name = ModelGeminiName.GEMINI_2_5_FLASH_LITE.value

        # Create model details
        model_details = {
            "provider": provider_value,
            "name": model_name,
            "parameters": model_params or {},
        }

        # Create session document
        session_document = {
            "session_id": session_id,
            "model": model_details,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "messages": [],
        }

        # Add card_ids if provided
        if card_ids is not None:
            session_document["card_ids"] = card_ids

        self.collection.insert_one(session_document)

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat session by ID.

        Args:
            session_id (str): The session ID

        Returns:
            Optional[Dict[str, Any]]: The chat session document or None if not found
        """
        return self.collection.find_one({"session_id": session_id})

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a chat session.

        Args:
            session_id (str): The session ID
            updates (Dict[str, Any]): The updates to apply

        Returns:
            bool: True if the session was updated, False otherwise
        """
        updates["updated_at"] = int(time.time())
        result = self.collection.update_one(
            {"session_id": session_id}, {"$set": updates}
        )
        return result.modified_count > 0

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.

        Args:
            session_id (str): The session ID

        Returns:
            bool: True if the session was deleted, False otherwise
        """
        result = self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0

    def get_sessions_by_card_id(self, card_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a specific card.

        Args:
            card_id (str): The card ID

        Returns:
            List[Dict[str, Any]]: List of chat sessions for the card
        """
        return list(self.collection.find({"card_ids": card_id}))

    def get_sessions_by_card_ids(self, card_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get all sessions that contain any of the specified card IDs.

        Args:
            card_ids (List[str]): List of card IDs

        Returns:
            List[Dict[str, Any]]: List of chat sessions containing any of the card IDs
        """
        return list(self.collection.find({"card_ids": {"$in": card_ids}}))

    def get_all_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all chat sessions with a limit.

        Args:
            limit (int): Maximum number of sessions to return

        Returns:
            List[Dict[str, Any]]: List of chat sessions
        """
        return list(self.collection.find({}).sort("created_at", -1).limit(limit))

    def add_message_to_session(
        self, session_id: str, role: str, content: str, timestamp: Optional[int] = None
    ) -> bool:
        """
        Add a message to a chat session.

        Args:
            session_id (str): The session ID
            role (str): The message role (user or assistant)
            content (str): The message content
            timestamp (Optional[int], optional): The message timestamp

        Returns:
            bool: True if the message was added, False otherwise
        """
        if timestamp is None:
            timestamp = int(time.time())

        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
        }

        result = self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": int(time.time())},
            },
        )
        return result.modified_count > 0

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat session.

        Args:
            session_id (str): The session ID

        Returns:
            List[Dict[str, Any]]: List of messages for the session
        """
        session = self.get_session(session_id)
        if session:
            return session.get("messages", [])
        return []

    def clear_session_messages(self, session_id: str) -> bool:
        """
        Clear all messages from a chat session.

        Args:
            session_id (str): The session ID

        Returns:
            bool: True if the messages were cleared, False otherwise
        """
        result = self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": [],
                    "updated_at": int(time.time()),
                }
            },
        )
        return result.modified_count > 0

    def get_sessions_by_date_range(
        self, start_timestamp: int, end_timestamp: int
    ) -> List[Dict[str, Any]]:
        """
        Get sessions created within a date range.

        Args:
            start_timestamp (int): Start timestamp
            end_timestamp (int): End timestamp

        Returns:
            List[Dict[str, Any]]: List of sessions in the date range
        """
        return list(
            self.collection.find(
                {
                    "created_at": {
                        "$gte": start_timestamp,
                        "$lte": end_timestamp,
                    }
                }
            ).sort("created_at", -1)
        )

    def get_session_count(self) -> int:
        """
        Get the total number of chat sessions.

        Returns:
            int: Total number of sessions
        """
        return self.collection.count_documents({})

    def get_sessions_by_model_provider(
        self, model_provider: ModelProvider
    ) -> List[Dict[str, Any]]:
        """
        Get sessions by model provider.

        Args:
            model_provider (ModelProvider): The model provider

        Returns:
            List[Dict[str, Any]]: List of sessions using the specified provider
        """
        provider_value = (
            model_provider.value
            if isinstance(model_provider, ModelProvider)
            else str(model_provider)
        )
        return list(
            self.collection.find({"model.provider": provider_value}).sort("created_at", -1)
        )
