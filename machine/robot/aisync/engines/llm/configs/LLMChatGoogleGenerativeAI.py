import os
from typing import Dict, Type

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from .base import LLMConfig


class LLMChatGoogleGenerativeAI(LLMConfig):
    _pyclass: Type = ChatGoogleGenerativeAI

    model: str = "gemini-1.0-pro-latest"
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    safety_setting: Dict = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
