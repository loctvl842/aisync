from typing import Literal, Optional

from pydantic_settings import BaseSettings


class AISyncSettings(BaseSettings):
    AISYNC_DEBUG: Optional[bool] = True
    AISYNC_LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] = "DEBUG"
    OPENAI_API_KEY: Optional[str] = None


class Settings(AISyncSettings):
    model_config = {"extra": "allow"}


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    return Settings(**kwargs)


env = get_settings()

__all__ = ["env"]
