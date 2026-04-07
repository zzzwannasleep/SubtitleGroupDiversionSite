from typing import Annotated

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    tracker_base_url: str = "http://localhost:2710/announce"
    tracker_credential_mode: str = "xbt_path"
    tracker_credential_query_key: str = "passkey"
    tracker_sync_mode: str = "xbt_db"
    tracker_user_stats_endpoint: str | None = None
    tracker_torrent_stats_endpoint: str | None = None
    tracker_sync_timeout_seconds: float = 10.0
    tracker_sync_interval_seconds: int = 60
    xbt_tracker_db_dsn: str | None = None
    allow_public_torrent_list: bool = True
    allow_user_registration: bool = True
    auto_create_tables: bool = True
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost", "http://localhost:5173"]
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if value.lstrip().startswith("["):
                import json

                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
