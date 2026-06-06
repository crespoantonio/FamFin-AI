import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.extraction_service import ExtractionService, ExtractionResult, ExtractionError
import ollama
from src.core.config import settings

@pytest.fixture
def mock_ollama_client():
    with patch("src.services.extraction_service.ollama.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def service(mock_ollama_client):
    # Reset singleton for testing
    ExtractionService._instance = None
    return ExtractionService()

@pytest.mark.anyio
async def test_extract_happy_path(service, mock_ollama_client):
    # Mocking the chat response
    mock_response = MagicMock()
    mock_response.message.content = '{"amount": 15.0, "category": "Food/Drink", "concept": "Starbucks", "currency": "USD"}'
    mock_ollama_client.chat.return_value = mock_response

    result = await service.extract("I spent $15 at Starbucks")

    assert isinstance(result, ExtractionResult)
    assert result.amount == 15.0
    assert result.category == "Food/Drink"
    assert result.concept == "Starbucks"
    assert result.currency == "USD"

    # Verify client chat was called correctly
    mock_ollama_client.chat.assert_called_once()
    kwargs = mock_ollama_client.chat.call_args.kwargs
    assert kwargs["model"] == settings.OLLAMA_MODEL
    assert "format" in kwargs

@pytest.mark.anyio
async def test_extract_currency_mapping(service, mock_ollama_client):
    mock_response = MagicMock()
    mock_response.message.content = '{"amount": 10.0, "category": "Food/Drink", "concept": "Lunch", "currency": "EUR"}'
    mock_ollama_client.chat.return_value = mock_response

    result = await service.extract("10 euros for lunch")

    assert result.amount == 10.0
    assert result.currency == "EUR"
    assert result.category == "Food/Drink"

@pytest.mark.anyio
async def test_extract_network_error(service, mock_ollama_client):
    mock_ollama_client.chat.side_effect = ollama.RequestError("Connection failed")

    with pytest.raises(ExtractionError, match="Failed to communicate with Ollama"):
        await service.extract("test")

@pytest.mark.anyio
async def test_extract_invalid_json(service, mock_ollama_client):
    mock_response = MagicMock()
    mock_response.message.content = 'invalid json'
    mock_ollama_client.chat.return_value = mock_response

    with pytest.raises(ExtractionError, match="Failed to parse extraction result"):
        await service.extract("test")

@pytest.mark.anyio
async def test_extract_empty_response(service, mock_ollama_client):
    mock_response = MagicMock()
    mock_response.message.content = ''
    mock_ollama_client.chat.return_value = mock_response

    with pytest.raises(ExtractionError, match="Received empty response"):
        await service.extract("test")
