from app.ai.base import AIProvider, AIProviderError
from app.ai.providers.demo_provider import DemoAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings, get_settings


def get_ai_provider(settings: Settings | None = None) -> AIProvider:
    cfg = settings or get_settings()
    if cfg.ai_provider == "demo":
        return DemoAIProvider()
    if cfg.ai_provider == "openai":
        return OpenAIProvider(cfg)
    raise AIProviderError(
        f"Unsupported AI_PROVIDER '{cfg.ai_provider}'",
        retryable=False,
    )
