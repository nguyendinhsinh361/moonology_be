import time
from typing import Any, Dict, List, Optional, TypedDict
import ast
import re
import json
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph

from app.core.constants import (
    DEFAULT_ERROR_RESPONSE,
    DEFAULT_MAX_TOKENS_GRAPH,
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_TEMPERATURE,
)
from app.enum.model import ModelGeminiName, ModelOpenAiName, ModelProvider
from app.models.llm_models import get_model
from app.models.memory import get_mongodb_chat_history
from app.utils.get_moonology_system_prompt import MoonologySystemPromptGenerator
from app.repositories.chat_user_request import ChatUserRequestRepository
import logging

logger = logging.getLogger(__name__)

# Cache for compiled graphs to avoid recompilation
_GRAPH_CACHE = {}


# Define state types for the graph
class ChatState(TypedDict):
    """State for the chat graph."""

    session_id: str
    user_input: str
    messages: List[BaseMessage]
    similar_knowledge: List[BaseMessage]
    detected_language: str
    response: Optional[str]
    model_provider: ModelProvider
    model_name: str
    temperature: Optional[float]
    max_tokens: int
    system_context: Optional[str]
    similarity_threshold: float
    model_params: Dict[str, Any]
    user_id: Optional[int]
    user_info: Optional[Dict[str, Any]]
    card_ids: Optional[List[str]]


def create_chat_graph():
    """
    Create a LangGraph for chat processing.
    Uses cached graph if available to avoid recompilation.

    Returns:
        StateGraph: A compiled LangGraph for chat processing
    """
    # Check if graph is already cached
    if "chat_graph" in _GRAPH_CACHE:
        return _GRAPH_CACHE["chat_graph"]

    # Build the graph
    workflow = StateGraph(ChatState)

    # Node 1: Load recent messages
    async def load_recent_messages(state: ChatState) -> ChatState:
        """Load recent messages from MongoDB."""
        mongodb_history = get_mongodb_chat_history(state["session_id"], max_messages=4)
        recent_messages = mongodb_history.messages

        # Store recent messages in state
        if "messages" not in state or not state["messages"]:
            state["messages"] = []

        if recent_messages:
            state["messages"].extend(recent_messages)

        return state

   # Node 2: Detect language
    async def detect_language(state: ChatState) -> ChatState:
        """Detect the language of user input using GPT."""
        try:
            # Get the language model for detection
            detection_llm = get_model(
                provider=ModelProvider.OPENAI,
                model_name=ModelOpenAiName.OPENAI_GPT_4_1_NANO.value,
                temperature=0.0,  # Use deterministic output
                max_tokens=10,
            )

            # Create system message
            prompt_generator = MoonologySystemPromptGenerator()
            messages = prompt_generator.generate_language_detection_prompt(
                state["user_input"]
            )

            # Get language detection
            detection_response = await detection_llm.ainvoke(messages)
            detected_language = detection_response.content.strip().lower()

            # Store detected language in state
            state["detected_language"] = detected_language
            print(f"Detected language: {detected_language}")

        except Exception as e:
            print(f"Error in language detection: {e}")
            # Default to Vietnamese if detection fails
            state["detected_language"] = "vietnamese"

        # Language mapping
        list_language = {
            "vietnamese": "tiếng việt",
            "english": "tiếng anh",
            "chinese": "tiếng trung",
            "korean": "tiếng hàn",
            "japanese": "tiếng nhật",
            "french": "tiếng pháp",
            "russian": "tiếng nga",
            "thai": "tiếng thái",
            "indonesian": "tiếng indonesia",
            "german": "tiếng đức",
            "india": "tiếng hindi",
            "malaysia": "tiếng malaysia",
            "portuguese": "tiếng bồ đào nha",
            "cambodia": "tiếng khmer",
            "netherlands": "tiếng hà lan",
            "spain": "tiếng tây ban nha",
        }

        # Map detected language to Vietnamese format
        detected_lang_lower = state["detected_language"].lower()
        for language in list_language.keys():
            if language in detected_lang_lower:
                state["detected_language"] = list_language[language]
                break
        else:
            # If no match found, default to Vietnamese
            state["detected_language"] = "tiếng anh"

        return state

    # Node 3: Search similar knowledge (disabled - no vector store)
    async def search_similar_knowledge(state: ChatState) -> ChatState:
        """Search for similar messages - currently disabled."""
        # Initialize similar_hsk_knowledge if not exists
        if "similar_hsk_knowledge" not in state:
            state["similar_hsk_knowledge"] = []

        # No vector search - return empty list
        state["similar_hsk_knowledge"] = []

        return state

    # Node 4: Load user info (if user_id is provided)
    async def load_user_info(state: ChatState) -> ChatState:
        """Load user information from chat_user_request collection."""
        if state.get("user_id"):
            # Save user request to chat_user_request table if user_id is provided
            user_request_repo = ChatUserRequestRepository()
            user_request_repo.save_user_request(state["user_id"], state["user_input"])

            user_info = user_request_repo.get_user_info(state["user_id"])
            state["user_info"] = user_info
        else:
            state["user_info"] = None

        return state

    # Node 5: Prepare system prompt
    async def prepare_system_prompt(state: ChatState) -> ChatState:
        """Prepare the system prompt with context."""
        # Generate base system prompt
        detected_lang = state.get("detected_language", "tiếng anh")

        # Handle case where user_info might be None
        user_about = None
        if state.get('user_info') and 'about_user' in state['user_info']:
            user_about = state['user_info']['about_user']
        
        prompt_generator = MoonologySystemPromptGenerator()
        system_prompt = prompt_generator.get_system_prompt(detected_lang.title(), user_about, state['system_context'])
        
        # Add information about similar messages and HSK knowledge
        if state.get("similar_hsk_knowledge"):
            system_prompt += prompt_generator.generate_context_prompt()
            for i, msg in enumerate(state["similar_hsk_knowledge"]):
                if hasattr(msg, "content"):
                    system_prompt += f"\n*KIẾN THỨC SỐ {i+1}*: \n{msg.content}\n"
        # Add closing note
        system_prompt += f'\n------------------------------\n### Hãy bắt đầu cuộc trò chuyện với sự nhập vai chân thực nhất với yêu cầu như sau: \n1. Ngôn ngữ: Trả lời bằng duy nhất bằng {detected_lang.title()}\n2. JSON FORMAT: {{"answer": "Câu trả lời của bạn bằng {detected_lang.title()}", "language": "{detected_lang.title()}"}}'

        # Create system message
        system_message = SystemMessage(content=system_prompt)

        # Ensure system message is at the beginning
        state["messages"] = [system_message] + [
            msg for msg in state["messages"] if not isinstance(msg, SystemMessage)
        ]

        return state

    # Node 6: Add user message
    async def add_user_message(state: ChatState) -> ChatState:
        """Add the user message to history and vector store."""
        # Create human message
        human_message = HumanMessage(content=state["user_input"])

        # Add to MongoDB history
        mongodb_history = get_mongodb_chat_history(state["session_id"])
        mongodb_history.add_message(human_message)

        # Add to state messages
        state["messages"].append(human_message)

        return state

    # Node 7: Generate response
    async def generate_response(state: ChatState) -> ChatState:
        """Generate a response using the LLM."""
        # Record start time for response time calculation
        start_time = time.time()

        # Configure model parameters
        model_kwargs = {
            "max_tokens": state["max_tokens"],
            "model_name": state["model_name"],
        }

        # Only add temperature if it's not None (for gpt-5-nano, temperature is set to None)
        if state["temperature"] is not None:
            model_kwargs["temperature"] = state["temperature"]

        # Add any additional model parameters from state
        if "model_params" in state and state["model_params"]:
            model_kwargs.update(state["model_params"])

        # Run name for tracing
        run_name = f"{state['model_name']}-graph-chat-{state['session_id']}"

        # Get the language model
        llm = get_model(provider=state["model_provider"], run_name=run_name, **model_kwargs)

        # Create prompt template based on model provider
        if state["model_provider"] == ModelProvider.GEMINI or (
            hasattr(state["model_provider"], "value")
            and state["model_provider"].value == ModelProvider.GEMINI.value
        ):
            prompt = ChatPromptTemplate.from_messages(
                [
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
        else:  # OpenAI
            prompt = ChatPromptTemplate.from_messages(
                [
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

        # Get the response from the LLM
        response = prompt.invoke({"messages": state["messages"]})
        chain_response = llm.invoke(response)
        content = chain_response.content.strip()
        if content.startswith("```json"):
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"\s*```", "", content)
        try:
            if content.startswith("{"):
                content = ast.literal_eval(content)["answer"]
            else:
                content = json.loads(content)["answer"]
        except Exception as e:
            logging.error(f"Error: {e}")
            content = content

        # Create AI message
        ai_message = AIMessage(content=content)

        # Add to state
        state["response"] = ai_message.content

        # Calculate and store response time in seconds (rounded to 2 decimal places)
        state["time_response"] = round(time.time() - start_time, 2)

        return state

    # Node 8: Save response
    async def save_response(state: ChatState) -> ChatState:
        """Save the AI response to history and vector store."""
        if state["response"]:
            # Create AI message
            ai_message = AIMessage(content=state["response"])

            # Add to MongoDB history with response time
            mongodb_history = get_mongodb_chat_history(state["session_id"])

            # Use the standard add_message method for the MongoDB history
            mongodb_history.add_message(ai_message)

            # Add to state messages
            state["messages"].append(ai_message)

        return state

    # Add nodes to the workflow
    workflow.add_node("load_recent_messages", load_recent_messages)
    workflow.add_node("detect_language", detect_language)
    workflow.add_node("search_similar_knowledge", search_similar_knowledge)
    workflow.add_node("load_user_info", load_user_info)
    workflow.add_node("prepare_system_prompt", prepare_system_prompt)
    workflow.add_node("add_user_message", add_user_message)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("save_response", save_response)

    # Define the edges
    workflow.set_entry_point("load_recent_messages")
    workflow.add_edge("load_recent_messages", "detect_language")
    workflow.add_edge("detect_language", "search_similar_knowledge")
    workflow.add_edge("search_similar_knowledge", "load_user_info")
    workflow.add_edge("load_user_info", "prepare_system_prompt")
    workflow.add_edge("prepare_system_prompt", "add_user_message")
    workflow.add_edge("add_user_message", "generate_response")
    workflow.add_edge("generate_response", "save_response")
    workflow.set_finish_point("save_response")

    # Compile the graph and cache it
    compiled_graph = workflow.compile()
    _GRAPH_CACHE["chat_graph"] = compiled_graph

    return compiled_graph


async def process_user_input(
    graph,
    user_input: str,
    session_id: str,
    model_provider: ModelProvider = ModelProvider.OPENAI,
    model_name: Optional[str] = None,
    temperature=DEFAULT_TEMPERATURE,
    max_tokens=DEFAULT_MAX_TOKENS_GRAPH,
    system_context: Optional[str] = None,
    similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD,
    model_params: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    card_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Process user input through the graph.

    Args:
        graph: The compiled LangGraph
        user_input (str): The user's input message
        session_id (str): The session ID for retrieving history
        model_provider (ModelProvider): The LLM provider to use
        model_name (Optional[str]): The specific model name to use
        temperature (float): Controls randomness in responses
        max_tokens (int): Maximum number of tokens in the response
        system_context (str, optional): Additional context for the system prompt
        similarity_threshold (float): Minimum similarity score for vector search
        model_params (Dict[str, Any], optional): Additional model parameters
        user_id (Optional[int], optional): User ID for retrieving user information
        card_ids (Optional[List[str]], optional): List of card IDs for context

    Returns:
        Dict[str, Any]: The response from the graph
    """
    # Set default model name based on provider if not provided
    if model_name is None:
        if model_provider == ModelProvider.OPENAI or (
            hasattr(model_provider, "value") and model_provider.value == ModelProvider.OPENAI.value
        ):
            model_name = ModelOpenAiName.OPENAI_GPT_4_1_NANO.value
        else:  # Default to Gemini
            model_name = ModelGeminiName.GEMINI_2_5_FLASH_LITE.value
    else:
        # Convert enum to string value if it's an enum
        model_name = model_name.value if hasattr(model_name, "value") else model_name

    # Prepare initial state
    config = ChatState(
        session_id=session_id,
        user_input=user_input,
        messages=[],
        similar_knowledge=[],
        detected_language="vietnamese",  # Default language
        response=None,
        model_provider=model_provider,
        model_name=model_name,
        temperature=None if model_name == ModelOpenAiName.OPENAI_GPT_5_NANO.value else temperature,
        max_tokens=max_tokens,
        system_context=system_context,
        similarity_threshold=similarity_threshold,
        model_params=model_params or {},
        user_id=user_id,
        user_info=None,
        card_ids=card_ids,
    )

    # Run the graph
    result = await graph.ainvoke(config)

    # Extract the final response
    if result and "response" in result:
        return {"output": result["response"]}
    else:
        return {"output": DEFAULT_ERROR_RESPONSE}
