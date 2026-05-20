"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    """Schema for creating new feedback."""
    customer_name: str
    customer_email: EmailStr
    feedback_text: str


class FeedbackResponse(BaseModel):
    """Schema for feedback responses."""
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    feedback_text: str
    sentiment: Optional[str] = None
    category: Optional[str] = None
    ai_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True