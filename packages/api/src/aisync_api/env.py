from pydantic_settings import BaseSettings

from pydantic import BaseModel, model_validator


class APISettings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_DEBUG: bool = False
    API_CORS_ALLOWED_ORIGINS: list = ["*"]


class SQLAlchemySettings(BaseModel):
    SQLALCHEMY_DATABASE_URI: str = "postgresql://postgres:thangcho@localhost:5432/aisync"
    SQLALCHEMY_ECHO: bool = False

    @staticmethod
    def _resolve_connection_uri(async_mode: bool, connection: str) -> str:
        from urllib.parse import urlparse, urlunparse

        postgres_parameters = urlparse(connection)
        scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg2"
        resolved_params = postgres_parameters._replace(scheme=scheme)

        return urlunparse(resolved_params)

    @model_validator(mode="after")
    def validate_model(self) -> "SQLAlchemySettings":
        self.SQLALCHEMY_DATABASE_URI = self._resolve_connection_uri(True, self.SQLALCHEMY_DATABASE_URI)
        return self


class Settings(
    APISettings,
    SQLAlchemySettings,
):
    model_config = {"extra": "allow"}


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    return Settings(**kwargs)


env = get_settings()

__all__ = ["env"]
