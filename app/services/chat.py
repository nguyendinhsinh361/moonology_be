"""
Chat service module.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import nest_asyncio

from app.core.constants import DEFAULT_MAX_TOKENS_GRAPH, DEFAULT_SIMILARITY_THRESHOLD
from app.enum.model import ModelGeminiName, ModelOpenAiName, ModelProvider
from app.graph.chat_graph import create_chat_graph, process_user_input
from app.repositories.chat_session import ChatSessionRepository
from app.services.memory import save_message_to_memory


def get_or_create_session(
    session_id: Optional[str] = None,
    model_provider: ModelProvider = ModelProvider.GEMINI,
    model_name: str = None,
    model_params: Dict[str, Any] = None,
    card_ids: Optional[List[str]] = None,
) -> str:
    """
    Get an existing session or create a new one.

    Args:
        session_id (str, optional): An existing session ID
        model_provider (ModelProvider): The LLM provider to use
        model_name (str, optional): The specific model name
        model_params (Dict[str, Any], optional): Additional model parameters
        card_ids (Optional[List[str]], optional): List of card IDs
    Returns:
        str: The session ID
    """

    repo = ChatSessionRepository()

    if session_id:
        # Check if the session exists
        session = repo.get_session(session_id)
        if session:
            return session_id

    # Set default model name based on provider if not provided
    if model_name is None or model_name == "":
        if model_provider == ModelProvider.OPENAI:
            model_name = ModelOpenAiName.OPENAI_GPT_4_1_NANO.value
        else:  # Default to Gemini
            model_name = ModelGeminiName.GEMINI_2_5_FLASH_LITE.value

    # Create a new session
    return repo.create_session(
        model_provider=model_provider,
        model_name=model_name,
        model_params=model_params,
        card_ids=card_ids,
    )


def chat_with_graph(
    user_input: str,
    session_id: Optional[str] = None,
    model_provider: ModelProvider = ModelProvider.OPENAI,
    model_name: str = None,
    model_params: Dict[str, Any] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS_GRAPH,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    system_context: Optional[str] = None,
    card_ids: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Chat with the user using the graph-based approach.
    Optimized for performance with cached graph and async execution.

    Args:
        user_input (str): The user's input message
        session_id (str, optional): An existing session ID
        model_provider (ModelProvider): The LLM provider to use
        model_name (str, optional): The specific model name
        model_params (Dict[str, Any], optional): Additional model parameters
        max_tokens (int): Maximum number of tokens in the response
        similarity_threshold (float): Minimum similarity score (0.0 to 1.0) for vector search
        system_context (str, optional): Additional context for the system prompt
        card_ids (Optional[List[str]], optional): List of card IDs

    Returns:
        Tuple[Dict[str, Any], str]: (response, session_id)
    """
    # Get or create a session
    session_id = get_or_create_session(
        session_id, model_provider, model_name, model_params, card_ids
    )

    # Save user message
    save_message_to_memory(session_id, "user", user_input)

    # Create the graph (will use cached version if available)
    graph = create_chat_graph()

    nest_asyncio.apply()

    # Sử dụng event loop hiện tại
    loop = asyncio.get_event_loop()

    # Process the user input with optimized async execution
    result = loop.run_until_complete(
        process_user_input(
            graph,
            user_input,
            session_id,
            model_provider=model_provider,
            model_name=model_name,
            max_tokens=max_tokens,
            system_context=system_context,
            similarity_threshold=similarity_threshold,
            model_params=model_params,
            card_ids=card_ids,
        )
    )

    # Save assistant response
    if "output" in result:
        save_message_to_memory(session_id, "assistant", result["output"])

    return result, session_id
