import logging
from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def get_ai_provider() -> AIProvider:
    """Factory creating configured AI provider based on environment variables."""
    provider_name = (settings.AI_PROVIDER or "mock").lower()

    if provider_name == "gemini":
        return GeminiProvider(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL_NAME)
    elif provider_name == "openai":
        return OpenAIProvider(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL_NAME)
    else:
        return MockAIProvider()
