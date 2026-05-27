from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "FamFin-AI"
    
    # Database
    DATABASE_URL: str
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # Security
    ENCRYPTION_KEY: str
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    MESSAGING_WEBHOOK_SECRET: str = ""
    
    # Configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
