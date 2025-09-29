from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.constants import DEFAULT_TEMPERATURE
from app.core.init import get_cached_model
from app.enum.model import ModelGeminiName, ModelOpenAiName, ModelProvider
from app.utils.langsmith import get_langsmith_tracer


def get_openai_model(
    model_name: ModelOpenAiName = ModelOpenAiName.OPENAI_GPT_4_1_NANO,
    temperature=DEFAULT_TEMPERATURE,
    max_tokens=None,
    run_name=None,
    use_cache=True,
) -> BaseChatModel:
    """
    Initialize and return an OpenAI chat model.

    Args:
        model_name (str): The name of the OpenAI model to use
        temperature (float): Controls randomness in responses
        max_tokens (int, optional): Maximum number of tokens to generate
        run_name (str, optional): Name for tracing runs
        use_cache (bool): Whether to use cached model if available

    Returns:
        ChatOpenAI: An instance of ChatOpenAI
    """
    # Ensure model_name is set
    if model_name is None:
        model_name = ModelOpenAiName.OPENAI_GPT_4_1_NANO

    # Check if we should use cached model with default settings
    if (
        use_cache
        and (model_name == ModelOpenAiName.OPENAI_GPT_4_1_NANO or 
             (hasattr(model_name, "value") and model_name.value == ModelOpenAiName.OPENAI_GPT_4_1_NANO.value) or
             str(model_name) == ModelOpenAiName.OPENAI_GPT_4_1_NANO.value)
        and temperature == DEFAULT_TEMPERATURE
        and max_tokens is None
    ):
        cached_model = get_cached_model("openai_model")
        if cached_model is not None:
            return cached_model

    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable."
        )

    # Convert enum to string value if it's an enum
    model_name_value = model_name.value if hasattr(model_name, "value") else str(model_name)

    callbacks = []
    if settings.LANGSMITH_TRACING:
        tracer = get_langsmith_tracer(run_name=run_name or f"openai-{model_name_value}")
        if tracer:
            callbacks.append(tracer)

    model_kwargs = {
        "model": model_name_value,
        "temperature": temperature,
        "api_key": settings.OPENAI_API_KEY,
        "callbacks": callbacks if callbacks else None,
    }

    if model_name_value == ModelOpenAiName.OPENAI_GPT_4_1_NANO.value:
        del model_kwargs["temperature"]

    # Add max_tokens if provided
    if max_tokens is not None:
        model_kwargs["max_tokens"] = max_tokens

    return ChatOpenAI(**model_kwargs)


def get_gemini_model(
    model_name: ModelGeminiName = ModelGeminiName.GEMINI_2_5_FLASH_LITE,
    temperature=DEFAULT_TEMPERATURE,
    max_tokens=None,
    run_name=None,
    use_cache=True,
) -> BaseChatModel:
    """
    Initialize and return a Google Gemini chat model.

    Args:
        model_name (str): The name of the Gemini model to use
        temperature (float): Controls randomness in responses
        max_tokens (int, optional): Maximum number of tokens to generate
        run_name (str, optional): Name for tracing runs
        use_cache (bool): Whether to use cached model if available

    Returns:
        ChatGoogleGenerativeAI: An instance of ChatGoogleGenerativeAI
    """
    # Ensure model_name is set
    if model_name is None:
        model_name = ModelGeminiName.GEMINI_2_5_FLASH_LITE

    # Check if we should use cached model with default settings
    if (
        use_cache
        and (model_name == ModelGeminiName.GEMINI_2_5_FLASH_LITE or 
             (hasattr(model_name, "value") and model_name.value == ModelGeminiName.GEMINI_2_5_FLASH_LITE.value) or
             str(model_name) == ModelGeminiName.GEMINI_2_5_FLASH_LITE.value)
        and temperature == DEFAULT_TEMPERATURE
        and max_tokens is None
    ):
        cached_model = get_cached_model("gemini_model")
        if cached_model is not None:
            return cached_model

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

    model_kwargs = {
        "model": model_name_value,
        "temperature": temperature,
        "google_api_key": settings.GOOGLE_API_KEY,
        "callbacks": callbacks if callbacks else None,
    }

    # Add max_tokens if provided
    if max_tokens is not None:
        model_kwargs["max_output_tokens"] = (
            max_tokens  # Gemini uses max_output_tokens instead of max_tokens
        )

    return ChatGoogleGenerativeAI(**model_kwargs)


def get_model(
    provider: ModelProvider = ModelProvider.GEMINI, run_name=None, **kwargs
) -> BaseChatModel:
    """
    Factory function to get the appropriate model based on provider.
    Uses cached models when possible for better performance.

    Args:
        provider (str): The model provider to use ('openai' or 'gemini')
        run_name (str, optional): Name for tracing runs
        **kwargs: Additional arguments to pass to the model initializer

    Returns:
        BaseChatModel: An instance of a chat model
    """
    # Get use_cache parameter if provided, default to True
    use_cache = kwargs.pop("use_cache", True)

    # Ensure model_name is set
    if "model_name" not in kwargs or kwargs["model_name"] is None:
        if provider == ModelProvider.OPENAI or (
            hasattr(provider, "value") and provider.value == ModelProvider.OPENAI.value
        ):
            kwargs["model_name"] = ModelOpenAiName.OPENAI_GPT_4_1_NANO.value
        else:
            kwargs["model_name"] = ModelGeminiName.GEMINI_2_5_FLASH_LITE.value

    if provider == ModelProvider.OPENAI or (
        hasattr(provider, "value") and provider.value == ModelProvider.OPENAI.value
    ):
        return get_openai_model(run_name=run_name, use_cache=use_cache, **kwargs)
    elif provider == ModelProvider.GEMINI or (
        hasattr(provider, "value") and provider.value == ModelProvider.GEMINI.value
    ):
        return get_gemini_model(run_name=run_name, use_cache=use_cache, **kwargs)
    else:
        raise ValueError(f"Unsupported model provider: {provider}. Use 'openai' or 'gemini'.")
