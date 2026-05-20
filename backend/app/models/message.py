"""
Message model for tracking individual chat messages in a feedback thread.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.feedback import Base


class Message(Base):
    """Message model - represents a single chat message."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey('feedback.id'), nullable=False)
    sender = Column(String(20), nullable=False)  # 'customer', 'agent', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    feedback = relationship("Feedback", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender}, feedback_id={self.feedback_id})>"
