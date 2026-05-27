from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.core.config import settings
from src.core.security import verify_messaging_secret
from src.services.messaging_service import MessagingService
from src.db.session import get_session
from sqlmodel import Session

router = APIRouter(prefix="/messages", tags=["Messages"])

class UserPayload(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class MessagePayload(BaseModel):
    text: Optional[str] = None
    message_id: int
    chat_id: int

class WebhookPayload(BaseModel):
    user: UserPayload
    message: MessagePayload

@router.post("")
@router.post("/")
async def receive_message(
    payload: WebhookPayload,
    x_famfin_token: Optional[str] = Header(None),
    session: Session = Depends(get_session)
):
    # Verify the secret token from n8n
    if not verify_messaging_secret(x_famfin_token):
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # Resolve or create the user and family
    service = MessagingService(session)
    user_data = {
        "id": payload.user.id,
        "username": payload.user.username,
        "first_name": payload.user.first_name,
        "last_name": payload.user.last_name
    }
    
    user, family = service.get_or_create_user_and_family(user_data)

    # Process command actions (e.g. welcome message on /start)
    text = payload.message.text or ""
    if text == "/start":
        welcome_text = (
            f"Welcome to {settings.PROJECT_NAME}, {payload.user.first_name or 'User'}!\n\n"
            "Your account is ready. You can now log your first expense by simply typing it, "
            "for example: '50 for lunch' or '100 for groceries'."
        )
        return {
            "status": "ok",
            "action": "reply",
            "text": welcome_text
        }

    return {"status": "ok", "user_id": str(user.id)}
