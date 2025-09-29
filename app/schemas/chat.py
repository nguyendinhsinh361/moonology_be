"""
Chat-related schemas.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.enum.model import ModelOpenAiName, ModelProvider


class Card(BaseModel):
    """Card schema."""

    id: Union[str, int] = Field(..., description="Card ID (can be string or number)")
    name: Optional[str] = Field(None, description="Card name")
    description: Optional[str] = Field(None, description="Card description")
    image_url: Optional[str] = Field(None, description="Card image URL")
    category: Optional[str] = Field(None, description="Card category")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Card keywords")


class ModelDetails(BaseModel):
    """Model details schema."""

    provider: ModelProvider = Field(
        ModelProvider.GEMINI, description="LLM provider (openai or gemini)"
    )
    name: Optional[str] = Field(None, description="Specific model name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")

    model_config = {
        "protected_namespaces": (),
        "use_enum_values": True,
        "json_schema_extra": {
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": [provider.value for provider in ModelProvider],
                    "default": ModelProvider.GEMINI.value,
                },
                "name": {"type": "string"},
                "parameters": {"type": "object"},
            }
        },
    }


class ChatRequest(BaseModel):
    """Chat request schema."""

    user_input: str = Field(default="Xin hãy giải thích ý nghĩa của các thẻ tôi bốc ra ở trên chi tiết giúp tôi", description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID (optional)")
    model_provider: ModelProvider = Field(
        ModelProvider.OPENAI, description="LLM provider (openai or gemini)"
    )
    model_name: Optional[str] = Field(
        ModelOpenAiName.OPENAI_GPT_4_1_NANO.value, description="Specific model name"
    )
    model_params: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    cards: Optional[List[Card]] = Field(default_factory=list, description="List of cards (optional)")

    model_config = {
        "protected_namespaces": (),
        "use_enum_values": True,
        "json_schema_extra": {
            "properties": {
                "model_provider": {
                    "type": "string",
                    "enum": [provider.value for provider in ModelProvider],
                    "default": ModelProvider.OPENAI.value,
                },
                "model_name": {"type": "string"},
                "model_params": {"type": "object"},
                "session_id": {"type": "string", "default": None},
                "user_input": {"type": "string", "default": None},
                "cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "image_url": {"type": "string"},
                            "category": {"type": "string"},
                            "keywords": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["id"]
                    },
                    "default": [],
                },
            }
        },
    }


class Message(BaseModel):
    """Chat message schema."""

    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[int] = Field(None, description="Message timestamp")


class ChatSession(BaseModel):
    """Chat session schema."""

    session_id: str = Field(..., description="Session ID")
    model: ModelDetails = Field(..., description="Model details")
    created_at: Optional[int] = Field(None, description="Creation timestamp")
    messages: List[Message] = Field(default_factory=list, description="Session messages")

    model_config = {"protected_namespaces": ()}


class ChatResponse(BaseModel):
    """Chat response schema."""

    response: Dict[str, Any] = Field(..., description="Response data")
    session_id: str = Field(..., description="Session ID")


class SuggestionRequest(BaseModel):
    """Suggestion request schema."""

    cards: Optional[List[Card]] = Field(default_factory=list, description="List of cards (optional)")
    session_id: Optional[str] = Field(None, description="Session ID (optional)")

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "properties": {
                "cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "image_url": {"type": "string"},
                            "category": {"type": "string"},
                            "keywords": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["id"]
                    },
                    "default": [],
                },
                "session_id": {"type": "string", "default": None},
            }
        },
    }


class SuggestionResponse(BaseModel):
    """Suggestion response schema."""

    total_suggestions: int = Field(..., description="Total number of suggestions")
    suggestions: List[str] = Field(..., description="List of suggestions")

    model_config = {"protected_namespaces": ()}
