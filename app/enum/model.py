from enum import Enum


class ModelProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelGeminiName(Enum):
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_THINKING = "gemini-2.0-flash-thinking"
    GEMINI_2_0_FLASH_EXP = "gemini-2.0-flash-exp"
    GEMINI_2_0_FLASH_THINKING_EXP = "gemini-2.0-flash-thinking-exp"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"


class ModelOpenAiName(Enum):
    OPENAI_GPT_4O_MINI = "gpt-4o-mini"
    OPENAI_GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"
    OPENAI_GPT_4_1_NANO = "gpt-4.1-nano"
    OPENAI_GPT_5_NANO = "gpt-5-nano"
