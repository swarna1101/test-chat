import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """
    Application settings model that provides configuration for all components.
    """

    # API key for accessing Google's Gemini AI service
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


# Create a global settings instance
settings = Settings()
logger.debug("settings", settings=settings.model_dump())
