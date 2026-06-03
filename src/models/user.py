from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    auth_token = Column(String, unique=True, nullable=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=True)
    telegram_linked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    boxes = relationship("Box", back_populates="user", cascade="all, delete-orphan")
    telegram_link_codes = relationship(
        "TelegramLinkCode", back_populates="user", cascade="all, delete-orphan"
    )
