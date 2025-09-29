"""
Suggestions service module.
"""

from typing import Dict, List, Optional

from app.core.config import settings
from app.models.memory import get_mongodb_chat_history
from app.utils.get_suggestions import generate_suggestions_moonology


def get_suggestions(cards_data: str, session_id: Optional[str] = None) -> Dict:
    """
    Generate suggestions based on cards data.

    Args:
        cards_data (str): The cards data to generate suggestions from
        session_id (Optional[str]): The session ID to get previous user questions

    Returns:
        Dict: Dictionary containing suggestions and total count
    """
    # Use the Google API key from settings
    api_key = settings.GOOGLE_API_KEY

    if not api_key:
        raise ValueError(
            "Google API key not configured. Set GOOGLE_API_KEY in environment variables."
        )

    # Get previous user questions if session_id is provided
    previous_questions = []
    if session_id:
        chat_history = get_mongodb_chat_history(session_id, max_messages=20, role_filter="user")
        if chat_history and chat_history.messages:
            previous_questions = [msg.content for msg in chat_history.messages]

    # Generate suggestions using the utility function
    result = generate_suggestions_moonology(cards_data, api_key, previous_questions)

    return result
