import os
from typing import Literal

from pydantic_settings import BaseSettings


class CoreSettings(BaseSettings):
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] = "DEBUG"


class TestSettings(BaseSettings):
    PYTEST: bool = False
    PYTEST_UNIT: bool = False


class DatabaseSettings(BaseSettings):
    SQLALCHEMY_POSTGRES_URI: str = "postgresql+asyncpg://postgres:thangcho@127.0.0.1:5432/aisync"
    SQLALCHEMY_ECHO: bool = False


class RedisSettings(BaseSettings):
    REDIS_URL: str = "redis://127.0.0.1:6379/0"


class OpenAISettings(BaseSettings):
    OPENAI_API_KEY: str = "sk-proj-1234567890abcdef1234567890abcdef"


class Settings(
    CoreSettings,
    TestSettings,
    DatabaseSettings,
    RedisSettings,
    OpenAISettings,
):
    model_config = {"extra": "allow"}


class DevelopmentSettings(Settings): ...


class ProductionSettings(Settings):
    DEBUG: bool = False


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    env = os.getenv("ENV", "development")
    setting_types = {
        "development": DevelopmentSettings(**kwargs),
        "production": ProductionSettings(**kwargs),
    }
    return setting_types[env]


settings = get_settings()
