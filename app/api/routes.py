"""
API routes module.
"""

import re
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Request
import logging

logger = logging.getLogger(__name__)

from app.enum.model import ModelProvider
from app.repositories.cards import CardsRepository
from app.repositories.chat_session import ChatSessionRepository
from app.schemas.chat import ChatRequest, ChatResponse, SuggestionRequest, SuggestionResponse
from app.services.chat import chat_with_graph
from app.services.suggestions import get_suggestions
from app.core.frontend_config import frontend_settings

# Create API router
router = APIRouter(prefix="/api")


def validate_model_provider(provider):
    """
    Validate and convert the model provider to the correct enum value.

    Args:
        provider: The provider value from the request

    Returns:
        ModelProvider: The validated ModelProvider enum
    """
    # If it's already an enum instance, return it
    if isinstance(provider, ModelProvider):
        return provider

    # If it's a string value, try to convert it
    if isinstance(provider, str):
        try:
            # Try to match by value
            for enum_provider in ModelProvider:
                if provider.lower() == enum_provider.value.lower():
                    return enum_provider

            # If no match found, raise error
            raise ValueError(f"Invalid model provider: {provider}")
        except Exception:
            raise ValueError(
                f"Invalid model provider: {provider}. Valid values are: {[p.value for p in ModelProvider]}"
            )

    # If we got here, the type is not supported
    raise ValueError(f"Unsupported model provider type: {type(provider)}")


def get_cards_context(card_ids: Optional[list]) -> Optional[str]:
    """
    Get cards context if card IDs are provided.

    Args:
        card_ids (Optional[list]): List of card IDs

    Returns:
        Optional[str]: Combined cards context if found, None otherwise
    """
    if not card_ids or len(card_ids) == 0:
        return None

    repo = CardsRepository()
    combined_context = ""
    
    for i, card_id in enumerate(card_ids):
        if card_id:  # Check if card_id is not None or empty
            card, context = repo.get_card_with_context(card_id)
            if context:
                if i > 0:
                    combined_context += "\n\n"
                combined_context += f"**Thẻ {i+1}**:\n{context}"

    return combined_context if combined_context else None


@router.get("/card/{card_id}")
async def get_card(card_id: str):
    """
    Get card information by ID.

    Args:
        card_id (str): Card ID

    Returns:
        dict: Card information and context
    """
    try:
        repo = CardsRepository()
        card, context = repo.get_card_with_context(card_id)

        if not card:
            raise HTTPException(
                status_code=404,
                detail=f"Card not found with ID {card_id}",
            )

        # Convert MongoDB document to JSON-serializable dict
        card_dict = {}
        if card:
            for key, value in card.items():
                # Convert ObjectId to string
                if key == "_id" and hasattr(value, "__str__"):
                    card_dict[key] = str(value)
                else:
                    card_dict[key] = value
            card_dict["card"] = card.get("card", "").replace("_", " ")

        return {"card": card_dict, "context": context}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving card: {str(e)}")


@router.post("/cards/by-ids")
async def get_cards_by_ids(card_ids: list[str]):
    """
    Get multiple cards by their IDs.

    Args:
        card_ids (list[str]): List of card IDs

    Returns:
        dict: List of cards and their information
    """
    try:
        if not card_ids:
            raise HTTPException(
                status_code=400,
                detail="Card IDs list cannot be empty",
            )

        repo = CardsRepository()
        cards_list = []
        not_found_ids = []

        for card_id in card_ids:
            card = repo.get_card_by_id(card_id)
            if card:
                # Convert MongoDB document to JSON-serializable dict
                card_dict = {}
                for key, value in card.items():
                    # Convert ObjectId to string
                    if key == "_id" and hasattr(value, "__str__"):
                        card_dict[key] = str(value)
                    else:
                        card_dict[key] = value
                card_dict["card"] = card.get("card", "").replace("_", " ")
                cards_list.append(card_dict)
            else:
                not_found_ids.append(card_id)

        # If some cards were not found, include them in the response
        response = {
            "cards": cards_list,
            "total_found": len(cards_list),
            "total_requested": len(card_ids),
            "not_found_ids": not_found_ids
        }

        # If no cards were found at all, return 404
        if len(cards_list) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No cards found with the provided IDs: {not_found_ids}",
            )

        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/cards")
async def get_all_cards():
    """
    Get all cards.

    Returns:
        dict: List of all cards
    """
    try:
        repo = CardsRepository()
        cards = repo.get_all_cards()

        # Convert MongoDB documents to JSON-serializable dicts
        cards_list = []
        for card in cards:
            card_dict = {}
            for key, value in card.items():
                # Convert ObjectId to string
                if key == "_id" and hasattr(value, "__str__"):
                    card_dict[key] = str(value)
                else:
                    card_dict[key] = value
            
            # Add image URLs from frontend
            card_title = card.get("card") or card.get("title", "")
            if card_title:
                card_dict["image_url"] = f"{frontend_settings.frontend_url}{frontend_settings.frontend_assets_path}/image_re/{card_title}.png"
                card_dict["card"] = card_title.replace("_", " ")
            
            cards_list.append(card_dict)

        return {"cards": cards_list, "total": len(cards_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/cards/category/{category}")
async def get_cards_by_category(category: str):
    """
    Get cards by category.

    Args:
        category (str): Category name

    Returns:
        dict: List of cards in the category
    """
    try:
        repo = CardsRepository()
        cards = repo.get_cards_by_category(category)

        # Convert MongoDB documents to JSON-serializable dicts
        cards_list = []
        for card in cards:
            card_dict = {}
            for key, value in card.items():
                # Convert ObjectId to string
                if key == "_id" and hasattr(value, "__str__"):
                    card_dict[key] = str(value)
                else:
                    card_dict[key] = value
            
            # Add image URLs from frontend
            card_title = card.get("card") or card.get("title", "")
            if card_title:
                card_dict["image_url"] = f"{frontend_settings.frontend_url}{frontend_settings.frontend_assets_path}/image_re/{card_title}.png"
                card_dict["card"] = card_title.replace("_", " ")
            
            cards_list.append(card_dict)

        return {"cards": cards_list, "total": len(cards_list), "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/cards/random")
async def get_random_card():
    """
    Get a random card.

    Returns:
        dict: Random card information
    """
    try:
        repo = CardsRepository()
        card = repo.get_random_card()

        if not card:
            raise HTTPException(
                status_code=404,
                detail="No cards found",
            )

        # Convert MongoDB document to JSON-serializable dict
        card_dict = {}
        for key, value in card.items():
            # Convert ObjectId to string
            if key == "_id" and hasattr(value, "__str__"):
                card_dict[key] = str(value)
            else:
                card_dict[key] = value
        
        # Add image URLs from frontend
        card_title = card.get("card") or card.get("title", "")
        if card_title:
            card_dict["image_url"] = f"{frontend_settings.frontend_url}{frontend_settings.frontend_assets_path}/image_re/{card_title}.png"
            card_dict["card"] = card_title.replace("_", " ")
        return {"card": card_dict}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving random card: {str(e)}")


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        200: {"description": "Successful chat response", "model": ChatResponse},
        201: {"description": "Successful chat response", "model": ChatResponse},
        400: {
            "description": "Bad request - Invalid model provider or request data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid model provider: invalid_provider. Valid values are: ['openai', 'gemini']"
                    }
                }
            },
        },
        404: {
            "description": "Card not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Card not found with ID card_123"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing request: Connection timeout"}
                }
            },
        },
    },
)
async def chat(request: ChatRequest = Body(...), request_obj: Request = None):
    """
    Chat endpoint.

    Args:
        request (ChatRequest): The chat request
        request_obj (Request): The FastAPI request object

    Returns:
        ChatResponse: The chat response with session_id and response data
    """
    try:
        # Validate the model provider
        validated_provider = validate_model_provider(request.model_provider)

        # Get cards context if provided
        cards_context = None
        card_ids = None
        if not request.cards:
            session_id = request.session_id
            chat_session = ChatSessionRepository()
            session_data = chat_session.get_session(session_id)
            if session_data and "card_ids" in session_data:
                card_ids = session_data["card_ids"]
            else:
                card_ids = []
        else:
            card_ids = [str(card.id) for card in request.cards]
            
        # Validate that all cards exist and get context
        if card_ids:
            card_repo = CardsRepository()
            for card_id in card_ids:
                card = card_repo.get_card_by_id(card_id)
                if not card:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Card not found with ID {card_id}",
                    )
                
            # Get combined context from all cards
            cards_context = get_cards_context(card_ids)
            
            
        # Use graph-based chat (removed simple chain option)
        response, session_id = chat_with_graph(
            request.user_input,
            request.session_id,
            model_provider=validated_provider,
            model_name=request.model_name,
            model_params=request.model_params,
            system_context=cards_context,
            card_ids=card_ids,
        )
        
        response["output"] = re.sub(r"```json|```|\*|\#", "", response["output"])
        response["output"] = re.sub(r"-{2,}", "", response["output"])
        response["output"] = re.sub(r"\n{2,}", "\n", response["output"])
        response["output"] = re.sub(r"_", " ", response["output"])
        return ChatResponse(response=response, session_id=session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post(
    "/suggestions",
    response_model=SuggestionResponse,
    responses={
        200: {"description": "Successful suggestions response", "model": SuggestionResponse},
        201: {"description": "Successful suggestions response", "model": SuggestionResponse},
        400: {
            "description": "Bad request - Invalid request data",
            "content": {
                "application/json": {"example": {"detail": "Invalid card data provided"}}
            },
        },
        404: {
            "description": "Card not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Card not found with ID card_123"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error generating suggestions: Service unavailable"}
                }
            },
        },
    },
)
async def generate_suggestions(request: SuggestionRequest = Body(...)):
    """
    Generate suggestions based on card data.

    Args:
        request (SuggestionRequest): The suggestion request containing card data or card reference

    Returns:
        SuggestionResponse: The suggestions response with total_suggestions and suggestions list
    """
    try:
        # Get cards context if cards reference is provided
        cards_data = None

        if request.cards and len(request.cards) > 0:
            # Extract card IDs from the cards list
            card_ids = [card.id for card in request.cards]
            
            # Validate that all cards exist
            card_repo = CardsRepository()
            for card_id in card_ids:
                card = card_repo.get_card_by_id(card_id)
                if not card:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Card not found with ID {card_id}",
                    )
            
            # Get combined context from all cards
            cards_data = get_cards_context(card_ids)

        # Ensure we have some cards data
        if not cards_data:
            return SuggestionResponse(
                total_suggestions=3,
                suggestions=[
                    "Hãy giải thích ý nghĩa của các thẻ này",
                    "Các thẻ này có liên quan gì đến nhau?",
                    "Làm thế nào để sử dụng các thẻ này trong thực tế?",
                ],
            )

        result = get_suggestions(cards_data, request.session_id)
        return SuggestionResponse(
            total_suggestions=result["total_suggestions"], suggestions=result["suggestions"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


# Root router (no prefix)
root_router = APIRouter()

