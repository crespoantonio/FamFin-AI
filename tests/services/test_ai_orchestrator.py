import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from src.services.ai_orchestrator import AIOrchestrator
from src.core.config import settings
from src.db.models import Transaction, User
from uuid import UUID
import datetime

@pytest.fixture
def orchestrator():
    return AIOrchestrator()

@pytest.mark.anyio
async def test_orchestrator_success_text(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_extract = AsyncMock()
    mock_extract_result = MagicMock()
    mock_extract_result.amount = 15.0
    mock_extract_result.currency = "USD"
    mock_extract_result.concept = "Starbucks"
    mock_extract_result.category = "Food/Drink"
    mock_extract_result.model_dump.return_value = {
        "amount": 15.0,
        "currency": "USD",
        "concept": "Starbucks",
        "category": "Food/Drink"
    }
    mock_extract.return_value = mock_extract_result

    class MockExtractionService:
        extract = mock_extract

    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)
    
    # Mock httpx.AsyncClient.post response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    
    # Needs to mock the context manager client without descriptor binding
    class MockClient:
        def __init__(self):
            self.post = mock_post
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    # Mock Session and EncryptionService
    mock_session = MagicMock()
    mock_session_class = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    monkeypatch.setattr("src.services.ai_orchestrator.Session", mock_session_class)
    
    class MockEncryptionService:
        def encrypt(self, text): return text
    monkeypatch.setattr(orchestrator, "encryption_service", MockEncryptionService())

    await orchestrator.orchestrate(user_id=user_id, text="15 for Starbucks", audio_url=None, chat_id=12345)
    
    # Extract service was called
    mock_extract.assert_called_once_with(text="15 for Starbucks")
    
    # httpx.post was called
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == settings.N8N_CALLBACK_URL
    assert call_args[1]["headers"]["X-FamFin-Token"] == settings.MESSAGING_WEBHOOK_SECRET
    payload = call_args[1]["json"]
    assert payload["status"] == "success"
    assert "Saved 15.0 USD for 'Starbucks' under category 'Food/Drink'." in payload["text"]
    assert payload["extracted_data"]["amount"] == 15.0

@pytest.mark.anyio
async def test_orchestrator_audio_success(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_transcribe = AsyncMock(return_value=("20 for taxi", "en"))
    class MockWhisperService:
        transcribe = mock_transcribe
    monkeypatch.setattr("src.services.ai_orchestrator.WhisperService", MockWhisperService)
    
    mock_extract = AsyncMock()
    mock_extract_result = MagicMock()
    mock_extract_result.amount = 20.0
    mock_extract_result.currency = "USD"
    mock_extract_result.concept = "Taxi"
    mock_extract_result.category = "Transport"
    mock_extract_result.model_dump.return_value = {"amount": 20.0}
    mock_extract.return_value = mock_extract_result

    class MockExtractionService:
        extract = mock_extract
    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    class MockClient:
        def __init__(self):
            self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    # Mock Session and EncryptionService
    mock_session = MagicMock()
    mock_session_class = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    monkeypatch.setattr("src.services.ai_orchestrator.Session", mock_session_class)
    
    class MockEncryptionService:
        def encrypt(self, text): return text
    monkeypatch.setattr(orchestrator, "encryption_service", MockEncryptionService())

    await orchestrator.orchestrate(user_id=user_id, text=None, audio_url="http://audio", chat_id=1)
    
    mock_transcribe.assert_called_once_with(audio_url="http://audio")
    mock_extract.assert_called_once_with(text="20 for taxi")
    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["status"] == "success"

@pytest.mark.anyio
async def test_orchestrator_transcription_failure(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_transcribe = AsyncMock(return_value=("", "en")) # triggers empty error
    class MockWhisperService:
        transcribe = mock_transcribe
    monkeypatch.setattr("src.services.ai_orchestrator.WhisperService", MockWhisperService)
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    class MockClient:
        def __init__(self):
            self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    await orchestrator.orchestrate(user_id=user_id, text=None, audio_url="http://audio", chat_id=1)
    
    payload = mock_post.call_args[1]["json"]
    assert payload["status"] == "error"
    assert "understand the audio" in payload["text"]

@pytest.mark.anyio
async def test_orchestrator_extraction_timeout(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_extract = AsyncMock(side_effect=Exception("Ollama timed out"))
    class MockExtractionService:
        extract = mock_extract
    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    class MockClient:
        def __init__(self):
            self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    await orchestrator.orchestrate(user_id=user_id, text="15 for Starbucks", audio_url=None, chat_id=12345)
    
    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["status"] == "error"
    assert "couldn't extract the details" in payload["text"]

@pytest.mark.anyio
async def test_orchestrator_callback_failure(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_extract = AsyncMock()
    mock_extract_result = MagicMock()
    mock_extract_result.amount = 15.0
    mock_extract_result.currency = "USD"
    mock_extract_result.concept = "Starbucks"
    mock_extract_result.category = "Food/Drink"
    mock_extract_result.model_dump.return_value = {"amount": 15.0}
    mock_extract.return_value = mock_extract_result
    class MockExtractionService:
        extract = mock_extract
    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)
    
    # Mock client post raising HTTP error
    mock_post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
    class MockClient:
        def __init__(self):
            self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    # This should not raise an exception because the orchestrator catches it
    await orchestrator.orchestrate(user_id=user_id, text="15 for Starbucks", audio_url=None, chat_id=12345)
    mock_post.assert_called_once()

@pytest.mark.anyio
async def test_orchestrator_persistence_success(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    family_id = "11111111-1111-1111-1111-111111111111"
    
    mock_extract = AsyncMock()
    mock_extract_result = MagicMock()
    mock_extract_result.amount = 15.0
    mock_extract_result.currency = "USD"
    mock_extract_result.concept = "Starbucks"
    mock_extract_result.category = "Food/Drink"
    mock_extract_result.model_dump.return_value = {"amount": 15.0}
    mock_extract.return_value = mock_extract_result
    
    class MockExtractionService:
        extract = mock_extract
    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    class MockClient:
        def __init__(self): self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    # Mock DB Session
    mock_session = MagicMock()
    mock_session_class = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    monkeypatch.setattr("src.services.ai_orchestrator.Session", mock_session_class)

    # Mock User query
    mock_user = MagicMock(family_id=UUID(family_id))
    mock_session.get.return_value = mock_user

    # Mock Encryption
    mock_encrypt = MagicMock()
    mock_encrypt.side_effect = lambda text: f"encrypted_{text}"
    class MockEncryptionService:
        def encrypt(self, text): return mock_encrypt(text)
    monkeypatch.setattr(orchestrator, "encryption_service", MockEncryptionService())

    await orchestrator.orchestrate(user_id=user_id, text="15 for Starbucks", audio_url=None, chat_id=12345)

    mock_session.get.assert_called_once_with(User, UUID(user_id))
    
    mock_session.add.assert_called_once()
    added_transaction = mock_session.add.call_args[0][0]
    assert isinstance(added_transaction, Transaction)
    assert added_transaction.user_id == UUID(user_id)
    assert added_transaction.family_id == UUID(family_id)
    assert added_transaction.amount == "encrypted_15.0 USD"
    assert added_transaction.concept == "encrypted_Starbucks"
    
    mock_session.commit.assert_called_once()

@pytest.mark.anyio
async def test_orchestrator_persistence_failure_rollback(orchestrator, monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_extract = AsyncMock()
    mock_extract_result = MagicMock()
    mock_extract_result.amount = 15.0
    mock_extract_result.currency = "USD"
    mock_extract_result.concept = "Starbucks"
    mock_extract_result.category = "Food/Drink"
    mock_extract.return_value = mock_extract_result
    class MockExtractionService:
        extract = mock_extract
    monkeypatch.setattr("src.services.ai_orchestrator.ExtractionService", MockExtractionService)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    class MockClient:
        def __init__(self): self.post = mock_post
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockClient())

    # Mock DB Session with commit failure
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("DB Error")
    mock_session_class = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    monkeypatch.setattr("src.services.ai_orchestrator.Session", mock_session_class)

    # Mock Encryption
    class MockEncryptionService:
        def encrypt(self, text): return f"encrypted_{text}"
    monkeypatch.setattr(orchestrator, "encryption_service", MockEncryptionService())

    await orchestrator.orchestrate(user_id=user_id, text="15 for Starbucks", audio_url=None, chat_id=12345)

    mock_session.rollback.assert_called_once()
    
    payload = mock_post.call_args[1]["json"]
    assert payload["status"] == "error"
    assert "Failed to save transaction" in payload["text"] or "An unexpected error occurred" in payload["text"]

