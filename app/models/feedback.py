"""
Database models for CustomerLens
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Feedback(Base):
    """Feedback model - represents a single customer feedback entry."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    feedback_text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=True)
    category = Column(String(50), nullable=True)
    ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="feedbacks")

    def __repr__(self):
        return f"<Feedback(id={self.id}, customer={self.customer_name})>"