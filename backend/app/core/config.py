from functools import lru_cache
from pathlib import Path

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
    upload_directory: str = Field(default="./data/uploads", alias="UPLOAD_DIRECTORY")
    frame_directory: str = Field(default="./data/frames", alias="FRAME_DIRECTORY")
    max_video_size_mb: int = Field(default=100, alias="MAX_VIDEO_SIZE_MB", ge=1)
    max_video_duration_seconds: int = Field(
        default=120,
        alias="MAX_VIDEO_DURATION_SECONDS",
        ge=1,
    )
    frame_sample_count: int = Field(default=10, alias="FRAME_SAMPLE_COUNT", ge=1, le=60)
    max_frame_dimension: int = Field(default=1280, alias="MAX_FRAME_DIMENSION", ge=320)

    ai_provider: str = Field(default="demo", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    vision_model: str | None = Field(default=None, alias="VISION_MODEL")
    ai_request_timeout_seconds: int = Field(
        default=45,
        alias="AI_REQUEST_TIMEOUT_SECONDS",
        ge=5,
        le=300,
    )
    ai_max_retries: int = Field(default=2, alias="AI_MAX_RETRIES", ge=0, le=5)
    ai_max_frames: int = Field(default=8, alias="AI_MAX_FRAMES", ge=1, le=16)
    ai_max_image_dimension: int = Field(
        default=1280,
        alias="AI_MAX_IMAGE_DIMENSION",
        ge=320,
        le=2048,
    )
    ai_demo_mode: bool = Field(default=True, alias="AI_DEMO_MODE")

    @field_validator("frontend_origins")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("FRONTEND_ORIGINS cannot be blank")
        if "*" in cleaned:
            raise ValueError("Wildcard CORS origins are not allowed")
        return cleaned

    @field_validator("ai_provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"demo", "openai"}:
            raise ValueError("AI_PROVIDER must be 'demo' or 'openai'")
        return cleaned

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_directory).expanduser().resolve()

    @property
    def frame_path(self) -> Path:
        return Path(self.frame_directory).expanduser().resolve()

    @property
    def is_demo_ai(self) -> bool:
        return self.ai_provider == "demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()
