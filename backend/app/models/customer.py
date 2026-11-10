"""Customer records shared by independent support tickets."""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.models.feedback import Base, utcnow


class Customer(Base):
    """Group tickets by a normalized email address."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    first_contact = Column(DateTime, default=utcnow)
    last_contact = Column(DateTime, default=utcnow, onupdate=utcnow)
    feedback_count = Column(Integer, default=0)
    feedbacks = relationship("Feedback", back_populates="customer")
