import os
from typing import Literal

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings


class CoreSettings(BaseSettings):
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 5000
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class PostgresSettings(BaseSettings):
    SQLALCHEMY_POSTGRES_URI: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/aisync"


class PGVectorSettings(BaseSettings):
    # SQLALCHEMY_PGVECTOR_URI: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5431/aisync"
    # Change your PGVECTOR URI here
    SQLALCHEMY_PGVECTOR_URI: str = "postgresql+asyncpg://postgres:12345@localhost:5431/aisync"


class RedisSettings(BaseSettings):
    REDIS_URL: str = "redis://127.0.0.1:6379/0"


class LangfuseSettings(BaseSettings):
    LANGFUSE_PUBLIC_KEY: str = "pk-lf-***"
    LANGFUSE_SECRET_KEY: str = "sk-lf-***"
    LANGFUSE_HOST: str = "https://cloud.langfuse.com/"


class OpenAISettings(BaseSettings):
    OPENAI_API_KEY: str = "sk-proj-1234567890abcdef1234567890abcdef"


class GoogleAISettings(BaseSettings):
    GOOGLE_API_KEY: str = "AIza1234567890abcdef1234567890abcdef"


class Settings(
    CoreSettings,
    PostgresSettings,
    PGVectorSettings,
    RedisSettings,
    LangfuseSettings,
    OpenAISettings,
    GoogleAISettings,
): ...


class DevelopmentSettings(Settings): ...


class ProductionSettings(Settings):
    DEBUG: bool = False


def get_settings() -> Settings:
    # Some LLMs require environment variables to be set.
    load_dotenv(find_dotenv())

    source = {"_env_file": ".env", "_env_file_encoding": "utf-8"}
    env = os.getenv("ENV", "development")
    setting_types = {
        "development": DevelopmentSettings(**source),
        "production": ProductionSettings(**source),
    }
    return setting_types[env]


settings = get_settings()
