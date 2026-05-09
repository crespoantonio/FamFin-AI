from fastapi import APIRouter, Request, Header, HTTPException, Depends
from telegram import Update, Bot
from src.core.config import settings
from src.core.security import verify_telegram_secret
from src.services.telegram_service import TelegramService
from src.db.session import get_session
from sqlmodel import Session

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Initialize bot instance once
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
    session: Session = Depends(get_session)
):
    # Verify secret token
    if not verify_telegram_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # Parse update
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    if not update.message or not update.message.from_user:
        return {"status": "ignored", "message": "No message or user data found"}

    # Handle registration
    service = TelegramService(session)
    user_data = {
        "id": update.message.from_user.id,
        "username": update.message.from_user.username,
        "first_name": update.message.from_user.first_name,
        "last_name": update.message.from_user.last_name
    }
    
    user, family = service.get_or_create_user_and_family(user_data)
    
    # Send welcome message if /start
    # Guard against None text for non-text messages
    text = update.message.text or ""
    if text == "/start":
        welcome_text = (
            f"Welcome to {settings.PROJECT_NAME}, {update.message.from_user.first_name}!\n\n"
            "Your account is ready. You can now log your first expense by simply typing it, "
            "for example: '50 for lunch' or '100 for groceries'."
        )
        await bot.send_message(chat_id=update.message.chat_id, text=welcome_text)
        return {"status": "ok", "message": "Welcome sent"}

    return {"status": "ok", "user_id": str(user.id)}
