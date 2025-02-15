from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_DEBUG: bool = False
    API_CORS_ALLOWED_ORIGINS: list = ["*"]


class Settings(APISettings):
    model_config = {"extra": "allow"}


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    return Settings(**kwargs)


env = get_settings()

__all__ = ["env"]
