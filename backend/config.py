"""Configuration management for the translation service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    openai_api_key: str
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
