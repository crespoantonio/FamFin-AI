import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
from src.db.session import get_session
from sqlmodel import Session, create_engine, SQLModel, select
from src.db.models import User
from sqlalchemy.pool import StaticPool

client = TestClient(app)

# Setup in-memory SQLite for testing
test_engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

def get_test_session():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = get_test_session

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

def test_webhook_invalid_secret():
    response = client.post(
        "/api/v1/telegram/webhook",
        json={},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid secret token"}

def test_webhook_missing_secret():
    response = client.post(
        "/api/v1/telegram/webhook",
        json={}
    )
    assert response.status_code == 403

def test_webhook_success_registration(monkeypatch):
    # Mock settings secret
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "valid-secret")
    
    # Mock payload
    payload = {
        "update_id": 1000,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Tony",
                "username": "tony_test"
            },
            "chat": {
                "id": 12345,
                "type": "private"
            },
            "date": 1620560000,
            "text": "/start"
        }
    }
    
    from unittest.mock import AsyncMock, MagicMock
    from telegram import Update
    
    # Mock the entire bot instance in the route module
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    monkeypatch.setattr("src.api.routes.telegram.bot", mock_bot)
    
    # Mock Update.de_json to return a mock update
    mock_update = MagicMock(spec=Update)
    mock_update.message.from_user.id = 12345
    mock_update.message.from_user.username = "tony_test"
    mock_update.message.from_user.first_name = "Tony"
    mock_update.message.from_user.last_name = None
    mock_update.message.text = "/start"
    mock_update.message.chat_id = 12345
    
    monkeypatch.setattr("telegram.Update.de_json", MagicMock(return_value=mock_update))
    
    # We expect a success response
    response = client.post(
        "/api/v1/telegram/webhook",
        json=payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "valid-secret"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome sent"}
    
    # Verify DB record creation
    with Session(test_engine) as session:
        user = session.exec(select(User).where(User.telegram_id == 12345)).first()
        assert user is not None
        assert user.username == "tony_test"
