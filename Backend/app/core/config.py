"""Application configuration from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    debug: bool = True

    # PostgreSQL async; set DATABASE_URL in env (postgresql+asyncpg://... or postgresql://... from Railway)
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/wishlist_ai"

    @field_validator("database_url", mode="after")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # CORS: allow localhost:3000 (frontend) and * for dev
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    github_client_id: str | None = None
    github_client_secret: str | None = None

    # Pushover (push notifications to wishlist owner)
    pushover_app_token: str | None = None

    # Pusher Channels (real-time; auth endpoint for private/presence channels)
    pusher_app_id: str | None = None
    pusher_key: str | None = None
    pusher_secret: str | None = None
    pusher_cluster: str = "ap2"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # Development: allow * so frontend (localhost:3000) can reach backend without CORS errors
        if self.app_env == "development":
            return ["*"]
        # Production: allow all origins for Vercel, or use CORS_ORIGINS env for specific list
        if self.app_env == "production":
            if origins and self.cors_origins != "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173":
                return origins
            return ["*"]
        return origins if origins else ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
