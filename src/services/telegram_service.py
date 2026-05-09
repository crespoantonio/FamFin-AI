from typing import Dict, Any, Tuple
from sqlmodel import Session, select
from src.db.models import User, Family

class TelegramService:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_user_and_family(self, telegram_user_data: Dict[str, Any]) -> Tuple[User, Family]:
        """
        Retrieves an existing user by telegram_id or creates a new User and Family.
        Updates user info (username, full_name) if it has changed.
        """
        telegram_id = telegram_user_data.get("id")
        if not telegram_id:
            raise ValueError("Telegram ID is required")

        username = telegram_user_data.get("username")
        first_name = telegram_user_data.get("first_name", "")
        last_name = telegram_user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or None

        # Check for existing user
        statement = select(User).where(User.telegram_id == telegram_id)
        user = self.session.exec(statement).first()

        if user:
            # Update info if changed
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.full_name != full_name:
                user.full_name = full_name
                changed = True
            
            if changed:
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)
            
            # Fetch family
            family = self.session.get(Family, user.family_id)
            return user, family

        # Create new Family and User in one atomic operation
        family_name = f"{full_name or username or 'User'}'s Family"
        family = Family(name=family_name)
        self.session.add(family)
        self.session.flush() # Get family.id without committing

        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            family_id=family.id
        )
        self.session.add(user)
        self.session.commit() # Atomic commit for both
        
        self.session.refresh(family)
        self.session.refresh(user)

        return user, family
