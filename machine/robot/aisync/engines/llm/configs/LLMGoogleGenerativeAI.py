import os
from typing import Dict, Type

from langchain_google_genai import GoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from .base import AisyncLLM


class LLMGoogleGenerativeAI(AisyncLLM):
    _pyclass: Type = GoogleGenerativeAI

    model: str = "gemini-pro"
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    safety_setting: Dict = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
