from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./linko-dev.db"
    jwt_secret_key: str = "dev-secret-key-for-local-development-only"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    google_client_id: str = "dev-google-client-id"
    youtube_api_key: str = "dev-youtube-api-key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
