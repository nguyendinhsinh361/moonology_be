"""
User summary service module.
"""

import logging
import os
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.enum.model import ModelGeminiName

# Set up logging
logger = logging.getLogger(__name__)


def summarize_user_info(about_user_newest: str, user_id: int) -> Optional[str]:
    """
    Extract user information based on their chat content using Gemini.

    Args:
        about_user_newest (str): About user newest
        user_id (int): User ID

    Returns:
        Optional[str]: Extracted user information in text format with 3 main sections or None if failed
    """
    try:
        if not about_user_newest:
            logger.warning(f"No content provided for user {user_id}")
            return None

        # Check if Google API key is available
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY environment variable is not set")
            return None

        # Initialize Gemini model
        model = ChatGoogleGenerativeAI(
            model=ModelGeminiName.GEMINI_2_5_FLASH_LITE.value,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=1000,
        )

        # Create system message
        system_message = SystemMessage(
            content="""
        Bạn là một AI chuyên gia trong việc trích xuất và phân tích thông tin người dùng từ các cuộc trò chuyện.
        Hãy trích xuất thông tin theo định dạng text với 3 mục chính như được yêu cầu.
        """
        )

        # Create prompt for information extraction
        prompt = f"""
        Dựa trên các câu hỏi và nội dung chat của người dùng dưới đây, hãy trích xuất thông tin về người dùng này:

        Thông tin hiện tại của người dùng và 5 đoạn chat gần nhất:
        {about_user_newest}

        Hãy trích xuất(bổ sung thêm nếu cần) và trả về thông tin theo định dạng text với 3 mục chính:

        1. Thông tin cơ bản:
        - Tên (nếu có đề cập)
        - Tên biệt danh (nếu có đề cập)
        - Tuổi (nếu có đề cập)
        - Gia đình (nếu có đề cập)
        - Tính cách (dựa vào các câu hỏi và nội dung chat của người dùng)
        - Quê quán (nếu có đề cập)
        - Giới tính (nếu có đề cập)
        - Trình độ học vấn (H1-H6, nếu có đề cập)
        - Nghề nghiệp hiện tại (nếu có đề cập)
        - Trường học (nếu có đề cập)
        - Nơi làm việc (nếu có đề cập)
        - Các thông tin khác (nếu có đề cập)

        2. Từ khóa tiếng Trung tôi thường xuyên hỏi:
        - Liệt kê các từ khóa tiếng Trung mà user thường hỏi (bao quát tất cả các từ khóa, không bỏ sót)

        3. Chủ đề tôi thường xuyên hỏi:
        - Liệt kê các chủ đề mà user thường hỏi (bao quát tất cả các chủ đề, không bỏ sót)

        Nếu không có thông tin nào được đề cập, hãy ghi "Không có thông tin" hoặc "Chưa có dữ liệu".
        Trả về kết quả dưới dạng text có cấu trúc rõ ràng với 3 mục trên.
        Không cần câu dẫn đầu, chỉ trả về kết quả.
        """

        # Create human message
        human_message = HumanMessage(content=prompt)

        # Generate summary using Gemini
        response = model.invoke([system_message, human_message])

        if response and hasattr(response, "content"):
            summary = response.content.strip()
            logger.info(f"Generated user info for user {user_id}: {summary[:100]}...")
            return (
                summary.replace("```json", "").replace("```", "").replace("*", "").replace("#", "")
            )
        else:
            logger.error(f"Invalid response from Gemini for user {user_id}")
            return None

    except Exception as e:
        logger.error(f"Error generating user info for user {user_id}: {str(e)}")
        return None
