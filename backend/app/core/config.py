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
    auth_rate_limit_enabled: bool = True
    auth_rate_limit_window_seconds: int = 60
    auth_login_rate_limit_attempts: int = 8
    auth_register_rate_limit_attempts: int = 5
    auto_create_tables: bool = True
    trusted_hosts: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    security_headers_enabled: bool = True
    hsts_enabled: bool = False
    hsts_max_age_seconds: int = 31536000
    session_cookie_secure: bool = False
    content_security_policy: str | None = None
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost", "http://localhost:5173"]
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        return cls._parse_csv_list(value)

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def parse_trusted_hosts(cls, value: str | list[str]) -> list[str]:
        return cls._parse_csv_list(value)

    @classmethod
    def _parse_csv_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if value.lstrip().startswith("["):
                import json

                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def validate_runtime_safety(self) -> None:
        if self.app_env.strip().lower() != "production":
            return

        unsafe_keys = []
        if self.secret_key in {"", "change-me"}:
            unsafe_keys.append("SECRET_KEY")
        if self.jwt_secret_key in {"", "change-me"}:
            unsafe_keys.append("JWT_SECRET_KEY")

        if unsafe_keys:
            joined_keys = ", ".join(unsafe_keys)
            raise RuntimeError(f"Production startup refused because insecure default secret(s) are set: {joined_keys}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
