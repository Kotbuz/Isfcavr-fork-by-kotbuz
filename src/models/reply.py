from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.db.database import Base


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedbacks.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    feedback = relationship("Feedback", back_populates="replies")
