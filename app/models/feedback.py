"""
Database models for CustomerLens
This file defines what our feedback data looks like in the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# This is the base class all our models inherit from
Base = declarative_base()


class Feedback(Base):
    """
    Feedback model - represents a single customer feedback entry.

    Think of this like a form with these fields:
    - ID (automatically generated)
    - Customer name
    - Customer email
    - The actual feedback text
    - When it was created
    - AI analysis results (we'll fill these in Days 2-4)
    """

    # Table name in database
    __tablename__ = "feedback"

    # Columns (fields)
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    feedback_text = Column(Text, nullable=False)

    # AI Analysis results (will be filled in later days)
    sentiment = Column(String(20), nullable=True)  # positive/negative/neutral/mixed
    category = Column(String(50), nullable=True)  # product/service/delivery/pricing
    ai_response = Column(Text, nullable=True)  # generated response

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        """String representation for debugging"""
        return f"<Feedback(id={self.id}, customer={self.customer_name})>"