from functools import lru_cache

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Trophy Store Backend"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    jwt_algorithm: str = "HS256"

    postgres_user: str = "postgres"
    postgres_password: str = "root"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "trophy_store"

    media_root: str = "storage"
    media_url: str = "/media"
    max_upload_size_mb: int = 10

    cors_origins: list[AnyUrl] | list[str] = ["http://localhost:3000", "http://localhost:5173","http://localhost:3001"]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
