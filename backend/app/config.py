from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings loaded from environment variables.
    
    Pydantic automatically:
    1. Reads from environment variables (case-insensitive)
    2. Falls back to .env file if variable not set
    3. Validates types (e.g., ensures DEBUG is a bool)
    4. Raises clear errors if required vars are missing
    """
    
    # AI Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # JIRA Configuration
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    
    # GitHub Configuration
    github_token: str = ""
    
    # Application Settings
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./team_monitor.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,      # OPENAI_API_KEY = openai_api_key
        extra="ignore"             # Ignore unknown env vars
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()
