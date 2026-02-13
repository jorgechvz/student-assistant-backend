"""Configuration module for the application settings."""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """This class uses Pydantic to load settings from environment variables."""

    app_name: str = Field("Student Learning Assistant Backend", alias="APP_NAME")
    app_description: str = Field(
        "This is a backend service for Student Learning Assistant",
        alias="APP_DESCRIPTION",
    )
    app_version: str = Field("1.0.0", alias="APP_VERSION")
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    env: Literal["local", "dev", "prod"] = Field("local", alias="ENV")

    azure_openai_endpoint: str = Field(
        ...,
        description="https://<resource-name>.openai.azure.com/",
        alias="AZURE_OPENAI_ENDPOINT",
    )
    azure_openai_key: str = Field(..., alias="AZURE_OPENAI_KEY")
    azure_openai_api_version: str = Field(..., alias="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment: str = Field(..., alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_model_name: str = Field(..., alias="AZURE_OPENAI_MODEL_NAME")
    azure_region: str = Field(..., alias="AZURE_REGION")
    azure_language: str = Field(..., alias="AZURE_LANGUAGE")
    azure_speech_voice: str = Field(..., alias="AZURE_SPEECH_VOICE")
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field(..., alias="MONGODB_DB_NAME")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_httponly: bool = Field(default=True, alias="COOKIE_HTTPONLY")
    cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", alias="COOKIE_SAMESITE"
    )
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"], alias="CORS_ORIGINS"
    )

    notion_client_id: str = Field(..., alias="NOTION_CLIENT_ID")
    notion_client_secret: str = Field(..., alias="NOTION_CLIENT_SECRET")
    notion_redirect_uri: str = Field(..., alias="NOTION_REDIRECT_URI")
    frontend_success_url: str = Field(..., alias="FRONTEND_SUCCESS_URL")

    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(..., alias="GOOGLE_REDIRECT_URI")
    frontend_google_success_url: str = Field(..., alias="FRONTEND_GOOGLE_SUCCESS_URL")
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings from environment variables.
    Uses LRU cache to avoid loading settings multiple times.
    """
    return Settings()
