import pytest
from src.core.security import verify_messaging_secret
from src.core.config import settings

def test_verify_messaging_secret_success():
    # Mock settings.MESSAGING_WEBHOOK_SECRET for the test
    original_secret = getattr(settings, "MESSAGING_WEBHOOK_SECRET", None)
    settings.MESSAGING_WEBHOOK_SECRET = "super-secret"
    
    try:
        assert verify_messaging_secret("super-secret") is True
    finally:
        if original_secret is not None:
            settings.MESSAGING_WEBHOOK_SECRET = original_secret

def test_verify_messaging_secret_failure():
    original_secret = getattr(settings, "MESSAGING_WEBHOOK_SECRET", None)
    settings.MESSAGING_WEBHOOK_SECRET = "super-secret"
    
    try:
        assert verify_messaging_secret("wrong-secret") is False
        assert verify_messaging_secret(None) is False
    finally:
        if original_secret is not None:
            settings.MESSAGING_WEBHOOK_SECRET = original_secret
