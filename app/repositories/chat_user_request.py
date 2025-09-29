"""
Chat user request repository module.
"""

import time
from typing import Any, Dict, List, Optional

from app.repositories.mongodb import MongoRepository
from app.utils.get_user_summary import summarize_user_info

MAX_CONTENT_COUNT = 5


class ChatUserRequestRepository(MongoRepository):
    """Repository for chat user requests."""

    def __init__(self):
        """Initialize the chat user request repository."""
        super().__init__("chat_user_request")

    def save_user_request(
        self,
        user_id: int,
        content: str,
    ) -> bool:
        """
        Save a user request to the database.
        If user_id already exists, append content to the existing array.
        If user_id doesn't exist, create new record with content as array.
        If content count reaches 5, generate user summary.

        Args:
            user_id (int): The user ID
            content (str): The user's question/content

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_time = int(time.time())

            # Check if user_id already exists
            existing_record = self.collection.find_one({"user_id": user_id})

            if existing_record:
                # Get current content array
                current_content = existing_record.get("content", [])
                about_user = existing_record.get("about_user", "")
                new_content = current_content + [content]
                new_content_newest = new_content[-5:]
                new_content_newest_str = "\n- ".join(new_content_newest)
                about_user_newest = f"**Thông tin hiện tại của người dùng**: {about_user}\n**5 đoạn chat gần nhất**: {new_content_newest_str}"

                # Check if we should generate summary (when count reaches 5)
                should_summarize = len(new_content) % MAX_CONTENT_COUNT == 0

                # Update existing record by adding content to the array
                update_data = {"$push": {"content": content}, "$set": {"updated_at": current_time}}

                # If we should generate summary, add about_user field
                if should_summarize:
                    summary = summarize_user_info(about_user_newest, user_id)
                    if summary:
                        update_data["$set"]["about_user"] = summary

                result = self.collection.update_one({"user_id": user_id}, update_data)
                return result.modified_count > 0
            else:
                # Create new record with content as array
                self.collection.insert_one(
                    {
                        "user_id": user_id,
                        "content": [content],  # Initialize as array
                        "created_at": current_time,
                        "updated_at": current_time,
                    }
                )
                return True
        except Exception as e:
            print(f"Error saving user request: {e}")
            return False

    def get_user_requests(
        self, user_id: int, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user requests by user ID.

        Args:
            user_id (int): The user ID
            limit (int): Maximum number of records to return
            skip (int): Number of records to skip

        Returns:
            List[Dict[str, Any]]: List of user requests
        """
        try:
            cursor = (
                self.collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            return list(cursor)
        except Exception as e:
            print(f"Error getting user requests: {e}")
            return []

    def get_all_user_requests(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all user requests.

        Args:
            limit (int): Maximum number of records to return
            skip (int): Number of records to skip

        Returns:
            List[Dict[str, Any]]: List of all user requests
        """
        try:
            cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"Error getting all user requests: {e}")
            return []

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information including about_user from chat_user_request collection.

        Args:
            user_id (int): The user ID

        Returns:
            Optional[Dict[str, Any]]: User information with about_user field or None if not found
        """
        try:
            user_record = self.collection.find_one({"user_id": user_id})
            if user_record:
                return {
                    "user_id": user_record.get("user_id"),
                    "about_user": user_record.get("about_user"),
                    "content_count": len(user_record.get("content", [])),
                    "created_at": user_record.get("created_at"),
                    "updated_at": user_record.get("updated_at"),
                }
            return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
