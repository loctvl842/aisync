from pydantic_settings import BaseSettings

from typing import Literal, Optional


class AISyncSettings(BaseSettings):
    AISYNC_DEBUG: Optional[bool] = True
    AISYNC_LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] = "DEBUG"


class LLMSettings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None


class Settings(AISyncSettings, LLMSettings):
    model_config = {"extra": "allow"}


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    return Settings(**kwargs)


env = get_settings()

__all__ = ["env"]
