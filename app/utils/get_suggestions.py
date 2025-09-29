"""
Suggestions utility module.

This module provides functions for generating suggestions based on card data.
"""

import re
from typing import Dict, List

import google.generativeai as genai

from app.core.config import settings
from app.enum.model import ModelGeminiName


def generate_suggestions_moonology(card_data: str, api_key: str, previous_questions: List[str] = None) -> Dict:
    """
    Generate suggestions based on card data using Google Gemini.

    Args:
        card_data (str): The card data to generate suggestions from
        api_key (str): Google API key
        previous_questions (List[str], optional): Previous questions to avoid repetition

    Returns:
        Dict: Dictionary containing suggestions and total count
    """
    try:
        # Configure Google Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(ModelGeminiName.GEMINI_2_5_FLASH_LITE.value)

        # Create context for the prompt
        context = f"""
Dựa trên dữ liệu thẻ Moonology sau đây, hãy tạo ra 3 gợi ý câu hỏi có thể khai thác để hỏi liên quan đến Moonology.

Dữ liệu thẻ:
{card_data}

Yêu cầu:
1. Câu hỏi phải liên quan trực tiếp đến thông tin thẻ
2. Câu hỏi phải có tính khám phá và học hỏi
3. Câu hỏi phù hợp với chủ đề Moonology

"""

        # Add previous questions context if available
        if previous_questions:
            context += f"\nCác câu hỏi trước đó (tránh lặp lại):\n"
            for i, question in enumerate(previous_questions[-3:], 1):  # Last 3 questions
                context += f"{i}. {question}\n"

        # Generate suggestions
        response = model.generate_content(context)
        suggestions_text = response.text

        # Parse suggestions (assuming they are numbered or bulleted)
        suggestions = []
        lines = suggestions_text.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            # Remove numbering or bullets
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                # Remove numbering/bullets and clean up
                clean_line = line.lstrip("0123456789.-* ").strip()
                if clean_line and len(clean_line) > 10:  # Minimum length check
                    clean_line = re.sub(r"```json|```|\*|\#", "", clean_line)
                    clean_line = re.sub(r"-{2,}", "", clean_line)
                    clean_line = re.sub(r"\n{2,}", "\n", clean_line)
                    clean_line = re.sub(r"_", " ", clean_line)
                    suggestions.append(clean_line)

        # Ensure we have exactly 3 suggestions
        if len(suggestions) > 3:
            suggestions = suggestions[:3]
        elif len(suggestions) < 3:
            # Add default suggestions if not enough
            default_suggestions = [
                "Hãy giải thích ý nghĩa của thẻ này",
                "Thẻ này có liên quan gì đến các thẻ khác?",
                "Làm thế nào để sử dụng thẻ này trong thực tế?"
            ]
            for default in default_suggestions:
                if default not in suggestions and len(suggestions) < 3:
                    suggestions.append(default)

        return {
            "total_suggestions": len(suggestions),
            "suggestions": suggestions
        }

    except Exception as e:
        # Return default suggestions on error
        default_suggestions = [
            "Hãy giải thích ý nghĩa của thẻ này",
            "Thẻ này có liên quan gì đến các thẻ khác?",
            "Làm thế nào để sử dụng thẻ này trong thực tế?"
        ]
        
        return {
            "total_suggestions": len(default_suggestions),
            "suggestions": default_suggestions
        }
