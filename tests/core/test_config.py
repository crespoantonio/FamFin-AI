import pytest
from pydantic import ValidationError
from src.core.config import settings, Settings

def test_whisper_configs_exist():
    # Verify these configs exist and are strings (so the test is not brittle to environmental values)
    assert hasattr(settings, "WHISPER_MODEL_SIZE")
    assert hasattr(settings, "WHISPER_DEVICE")
    assert hasattr(settings, "WHISPER_COMPUTE_TYPE")
    assert isinstance(settings.WHISPER_MODEL_SIZE, str)
    assert isinstance(settings.WHISPER_DEVICE, str)
    assert isinstance(settings.WHISPER_COMPUTE_TYPE, str)

def test_n8n_callback_url_validation():
    # Valid url
    s = Settings(
        DATABASE_URL="postgresql+psycopg://user:pass@db/db",
        ENCRYPTION_KEY="testkey",
        N8N_CALLBACK_URL="http://localhost:5678/webhook/famfin-callback"
    )
    assert s.N8N_CALLBACK_URL == "http://localhost:5678/webhook/famfin-callback"

    # Invalid protocol
    with pytest.raises(ValidationError, match="must start with http:// or https://"):
        Settings(
            DATABASE_URL="postgresql+psycopg://user:pass@db/db",
            ENCRYPTION_KEY="testkey",
            N8N_CALLBACK_URL="ftp://localhost:5678"
        )
    
    # Missing host
    with pytest.raises(ValidationError, match="must contain a valid host"):
        Settings(
            DATABASE_URL="postgresql+psycopg://user:pass@db/db",
            ENCRYPTION_KEY="testkey",
            N8N_CALLBACK_URL="http://"
        )
