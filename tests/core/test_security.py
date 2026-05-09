import pytest
from src.core.security import verify_telegram_secret
from src.core.config import settings

def test_verify_telegram_secret_success():
    # Mock settings.TELEGRAM_WEBHOOK_SECRET for the test
    original_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    settings.TELEGRAM_WEBHOOK_SECRET = "super-secret"
    
    try:
        assert verify_telegram_secret("super-secret") is True
    finally:
        if original_secret is not None:
            settings.TELEGRAM_WEBHOOK_SECRET = original_secret

def test_verify_telegram_secret_failure():
    original_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    settings.TELEGRAM_WEBHOOK_SECRET = "super-secret"
    
    try:
        assert verify_telegram_secret("wrong-secret") is False
        assert verify_telegram_secret(None) is False
    finally:
        if original_secret is not None:
            settings.TELEGRAM_WEBHOOK_SECRET = original_secret
