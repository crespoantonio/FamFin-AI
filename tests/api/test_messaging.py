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
        "/api/v1/messages",
        json={
            "user": {"id": 12345, "username": "tony_test", "first_name": "Tony"},
            "message": {"text": "/start", "message_id": 1, "chat_id": 12345}
        },
        headers={"X-FamFin-Token": "wrong-secret"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid secret token"}

def test_webhook_missing_secret():
    response = client.post(
        "/api/v1/messages",
        json={
            "user": {"id": 12345, "username": "tony_test", "first_name": "Tony"},
            "message": {"text": "/start", "message_id": 1, "chat_id": 12345}
        }
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid secret token"}

def test_webhook_success_registration(monkeypatch):
    # Mock settings secret
    monkeypatch.setattr(settings, "MESSAGING_WEBHOOK_SECRET", "valid-secret")
    
    # Mock payload
    payload = {
        "user": {
            "id": 12345,
            "username": "tony_test",
            "first_name": "Tony",
            "last_name": "Crespo"
        },
        "message": {
            "text": "/start",
            "message_id": 1,
            "chat_id": 12345
        }
    }
    
    # We expect a success response with standardized welcome action
    response = client.post(
        "/api/v1/messages",
        json=payload,
        headers={"X-FamFin-Token": "valid-secret"}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "ok"
    assert res_data["action"] == "reply"
    assert "Welcome to FamFin-AI" in res_data["text"]
    
    # Verify DB record creation
    with Session(test_engine) as session:
        user = session.exec(select(User).where(User.telegram_id == 12345)).first()
        assert user is not None
        assert user.username == "tony_test"
        assert user.full_name == "Tony Crespo"
