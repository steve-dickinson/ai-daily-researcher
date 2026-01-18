from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Daily Researcher"
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27019"
    POSTGRES_URL: str = "postgresql+asyncpg://user:password@localhost:5433/researcher"
    
    # AI
    AI_PROVIDER: str = "mock" # options: "mock", "openai", "gemini"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini" # default to a high-context model
    GEMINI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
