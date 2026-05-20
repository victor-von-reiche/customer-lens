"""
Customer model for tracking repeat customers.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.feedback import Base


class Customer(Base):
    """Customer model - tracks unique customers by email."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    feedback_count = Column(Integer, default=0)

    feedbacks = relationship("Feedback", back_populates="customer")