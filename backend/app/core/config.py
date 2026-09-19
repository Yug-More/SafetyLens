from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="SafetyLens API", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="sqlite:///./safetylens.db",
        alias="DATABASE_URL",
    )
    frontend_origins: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_ORIGINS",
    )
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    @field_validator("frontend_origins")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("FRONTEND_ORIGINS cannot be blank")
        if "*" in cleaned:
            raise ValueError("Wildcard CORS origins are not allowed")
        return cleaned

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
