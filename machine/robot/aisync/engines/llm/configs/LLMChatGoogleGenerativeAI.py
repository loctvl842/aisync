import os
from typing import Dict, Type

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from .base import AisyncLLM


class LLMChatGoogleGenerativeAI(AisyncLLM):
    _pyclass: Type = ChatGoogleGenerativeAI

    model: str = "gemini-1.5-flash"
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    safety_setting: Dict = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
