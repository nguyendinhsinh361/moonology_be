"""
LLM models service.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.constants import DEFAULT_TEMPERATURE
from app.core.langsmith import get_langsmith_tracer
from app.enum.model import ModelGeminiName, ModelOpenAiName, ModelProvider


def get_openai_model(
    model_name: ModelOpenAiName = ModelOpenAiName.OPENAI_GPT_4_1_NANO,
    temperature=DEFAULT_TEMPERATURE,
    run_name=None,
) -> BaseChatModel:
    """
    Initialize and return an OpenAI chat model.

    Args:
        model_name (str): The name of the OpenAI model to use
        temperature (float): Controls randomness in responses
        run_name (str, optional): Name for tracing runs

    Returns:
        ChatOpenAI: An instance of ChatOpenAI
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable."
        )

    callbacks = []
    if settings.LANGSMITH_TRACING:
        # Convert enum to string value if it's an enum
        model_name_value = model_name.value if hasattr(model_name, "value") else str(model_name)
        tracer = get_langsmith_tracer(run_name=run_name or f"openai-{model_name_value}")
        if tracer:
            callbacks.append(tracer)
            
    # Convert enum to string value if it's an enum
    model_name_value = model_name.value if hasattr(model_name, "value") else str(model_name)
    
    config_openai = {
        "model_name": model_name_value,
        "temperature": temperature,
        "api_key": settings.OPENAI_API_KEY,
        "callbacks": callbacks if callbacks else None,
    }
    
    if model_name_value == ModelOpenAiName.OPENAI_GPT_4_1_NANO.value:
        del config_openai["temperature"]

    return ChatOpenAI(**config_openai)


def get_gemini_model(
    model_name: ModelGeminiName = ModelGeminiName.GEMINI_2_5_FLASH_LITE,
    temperature=DEFAULT_TEMPERATURE,
    run_name=None,
) -> BaseChatModel:
    """
    Initialize and return a Google Gemini chat model.

    Args:
        model_name (str): The name of the Gemini model to use
        temperature (float): Controls randomness in responses
        run_name (str, optional): Name for tracing runs

    Returns:
        ChatGoogleGenerativeAI: An instance of ChatGoogleGenerativeAI
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError(
            "Google API key is not set. Please set the GOOGLE_API_KEY environment variable."
        )

    # Convert enum to string value if it's an enum
    model_name_value = model_name.value if hasattr(model_name, "value") else str(model_name)
    
    callbacks = []
    if settings.LANGSMITH_TRACING:
        tracer = get_langsmith_tracer(run_name=run_name or f"gemini-{model_name_value}")
        if tracer:
            callbacks.append(tracer)

    return ChatGoogleGenerativeAI(
        model=model_name_value,
        temperature=temperature,
        google_api_key=settings.GOOGLE_API_KEY,
        callbacks=callbacks if callbacks else None,
    )


def get_model(
    provider: ModelProvider = ModelProvider.GEMINI, run_name=None, **kwargs
) -> BaseChatModel:
    """
    Factory function to get the appropriate model based on provider.

    Args:
        provider (ModelProvider): The model provider to use (ModelProvider.OPENAI or ModelProvider.GEMINI)
        run_name (str, optional): Name for tracing runs
        **kwargs: Additional arguments to pass to the model initializer

    Returns:
        BaseChatModel: An instance of a chat model
    """
    if provider == ModelProvider.OPENAI or (
        hasattr(provider, "value") and provider.value == ModelProvider.OPENAI.value
    ):
        return get_openai_model(run_name=run_name, **kwargs)
    elif provider == ModelProvider.GEMINI or (
        hasattr(provider, "value") and provider.value == ModelProvider.GEMINI.value
    ):
        return get_gemini_model(run_name=run_name, **kwargs)
    else:
        raise ValueError(f"Unsupported model provider: {provider}. Use 'openai' or 'gemini'.")
