from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "pt-platform"
    app_env: str = "development"
    secret_key: str = "change-me"
    jwt_secret_key: str = "change-me"
    jwt_expire_minutes: int = 1440
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    torrent_storage_path: str = "/app/data/torrents"
    upload_storage_path: str = "/app/data/uploads"
    public_web_base_url: str = "http://localhost"
    tracker_impl: str = "xbt"
    tracker_base_url: str = "http://localhost/announce"
    tracker_credential_mode: str = "path"
    tracker_credential_query_key: str = "passkey"
    tracker_sync_mode: str = "pull"
    tracker_user_stats_endpoint: str | None = None
    tracker_torrent_stats_endpoint: str | None = None
    tracker_sync_timeout_seconds: float = 10.0
    allow_public_torrent_list: bool = True
    allow_user_registration: bool = True
    auto_create_tables: bool = True
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost", "http://localhost:5173"])

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
