import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from src.db.models import Family, User, Transaction
import uuid
from datetime import datetime, timezone

# Setup in-memory SQLite for testing models
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_family(session: Session):
    family = Family(name="Test Family")
    session.add(family)
    session.commit()
    session.refresh(family)
    
    assert family.id is not None
    assert isinstance(family.id, uuid.UUID)
    assert family.name == "Test Family"

def test_create_user_in_family(session: Session):
    family = Family(name="Smiths")
    session.add(family)
    session.commit()
    
    user = User(
        telegram_id=123456789,
        username="john_smith",
        family_id=family.id
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    assert user.id is not None
    assert user.family_id == family.id
    assert user.family.name == "Smiths"
    assert len(family.users) == 1

def test_create_transaction(session: Session):
    family = Family(name="Budget Family")
    session.add(family)
    session.commit()
    
    user = User(telegram_id=999, family_id=family.id)
    session.add(user)
    session.commit()
    
    # Ciphertext strings (simulating EncryptionService output)
    encrypted_amount = "gAAAAABm..."
    encrypted_concept = "gAAAAABn..."
    
    transaction = Transaction(
        family_id=family.id,
        user_id=user.id,
        amount=encrypted_amount,
        concept=encrypted_concept,
        category="Food",
        timestamp=datetime.now(timezone.utc)
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.amount == encrypted_amount
    assert transaction.family_id == family.id
    assert transaction.user_id == user.id
    
def test_family_transaction_relationship(session: Session):
    family = Family(name="Relation Family")
    session.add(family)
    session.commit()
    
    user = User(telegram_id=1, family_id=family.id)
    session.add(user)
    
    t1 = Transaction(family_id=family.id, user_id=user.id, amount="10", concept="A", category="X")
    t2 = Transaction(family_id=family.id, user_id=user.id, amount="20", concept="B", category="Y")
    session.add(t1)
    session.add(t2)
    session.commit()
    
    session.refresh(family)
    assert len(family.transactions) == 2

def test_transaction_requires_family(session: Session):
    # This should fail if family_id is mandatory and no family is provided
    # Note: SQLModel/SQLAlchemy only enforces this on commit/flush if nullable=False
    with pytest.raises(Exception):
        t = Transaction(amount="10", concept="A", category="X")
        session.add(t)
        session.commit()
