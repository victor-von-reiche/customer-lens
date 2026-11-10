"""Messages inside a support ticket."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.feedback import Base, utcnow


class Message(Base):
    """Store a customer message or a reviewed support response."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    feedback = relationship("Feedback", back_populates="messages")
