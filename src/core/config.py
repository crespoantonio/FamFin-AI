from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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
    
    # Whisper settings
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    @field_validator("WHISPER_DEVICE")
    @classmethod
    def validate_whisper_device(cls, v: str) -> str:
        allowed = {"cpu", "cuda", "auto"}
        if v.lower() not in allowed:
            raise ValueError(f"WHISPER_DEVICE must be one of {allowed}")
        return v.lower()

    @field_validator("WHISPER_COMPUTE_TYPE")
    @classmethod
    def validate_whisper_compute_type(cls, v: str) -> str:
        allowed = {"int8", "int8_float16", "int16", "float16", "float32", "default"}
        if v.lower() not in allowed:
            raise ValueError(f"WHISPER_COMPUTE_TYPE must be one of {allowed}")
        return v.lower()
        
    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def validate_ollama_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
        return v

    @field_validator("OLLAMA_MODEL")
    @classmethod
    def validate_ollama_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("OLLAMA_MODEL cannot be empty")
        return v.strip()
    
    # Configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
