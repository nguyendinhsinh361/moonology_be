"""
Cards repository module.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from app.repositories.mongodb import MongoRepository


class CardsRepository(MongoRepository):
    """Repository for Moonology cards."""

    def __init__(self):
        """Initialize the cards repository."""
        super().__init__("cards")

    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a card by ID.

        Args:
            card_id (str): The card ID

        Returns:
            Optional[Dict[str, Any]]: The card document or None if not found
        """
        # Try to convert to int if possible, otherwise use as string
        try:
            card_id_int = int(card_id)
            return self.collection.find_one({"id": card_id_int})
        except (ValueError, TypeError):
            return self.collection.find_one({"id": card_id})

    def get_card_with_context(self, card_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get a card by ID along with a system context.

        Args:
            card_id (str): The card ID

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]:
                - The card document or None if not found
                - A system context string based on the card or None if not found
        """
        card = self.get_card_by_id(card_id)

        if not card:
            return None, None

        # Create system context based on the card data
        context = ""

        # Map field names to Vietnamese labels and only include fields with values
        field_labels = {
            "card": "- Tên thẻ: ",
            "short_meam": "\n- Ý nghĩa: ",
            "kind": "\n- Loại: ",
            "content": "\n- Nội dung: ",
        }

        for field, label in field_labels.items():
            if field == "content" and field in card and card[field]:
                content_obj = card[field]
                context += label
                
                # Handle nested fields in content
                if "overall_meaning" in content_obj:
                    context += f"\n  - Ý nghĩa tổng thể: {content_obj['overall_meaning']}"
                
                if "attune_to_the_moon" in content_obj:
                    context += f"\n  - Điều chỉnh theo mặt trăng: {content_obj['attune_to_the_moon']}"
                
                if "additional_meanings" in content_obj and content_obj["additional_meanings"]:
                    context += "\n  - Ý nghĩa bổ sung:"
                    for meaning in content_obj["additional_meanings"]:
                        context += f"\n    • {meaning}"
                
                if "the_teaching" in content_obj:
                    context += f"\n  - Giáo lý: {content_obj['the_teaching']}"
            elif field in card and card[field] not in ["", None, []]:
                context += f"{label}{card[field]}"

        return card, context

    def get_all_cards(self) -> List[Dict[str, Any]]:
        """
        Get all cards.

        Returns:
            List[Dict[str, Any]]: List of all cards
        """
        return list(self.collection.find({}))

    def get_cards_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get cards by category.

        Args:
            category (str): The category to filter by

        Returns:
            List[Dict[str, Any]]: List of cards in the specified category
        """
        return list(self.collection.find({"category": category}))

    def search_cards_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search cards by keywords.

        Args:
            keywords (List[str]): List of keywords to search for

        Returns:
            List[Dict[str, Any]]: List of cards matching the keywords
        """
        # Create a regex pattern to match any of the keywords
        regex_pattern = "|".join(keywords)
        return list(self.collection.find({"keywords": {"$regex": regex_pattern, "$options": "i"}}))

    def get_random_card(self) -> Optional[Dict[str, Any]]:
        """
        Get a random card.

        Returns:
            Optional[Dict[str, Any]]: A random card or None if no cards exist
        """
        return self.collection.aggregate([{"$sample": {"size": 1}}]).next()

    def get_cards_by_name_pattern(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Get cards by name pattern.

        Args:
            name_pattern (str): The name pattern to search for

        Returns:
            List[Dict[str, Any]]: List of cards matching the name pattern
        """
        return list(self.collection.find({"name": {"$regex": name_pattern, "$options": "i"}}))
