"""
Pydantic schemas for request/response validation
These define what data looks like coming in and going out of our API
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    """
    Schema for creating new feedback.
    This is what the API expects when someone submits feedback.
    """
    customer_name: str
    customer_email: EmailStr  # Validates it's a real email format
    feedback_text: str


class FeedbackResponse(BaseModel):
    """
    Schema for feedback responses.
    This is what the API sends back after storing feedback.
    """
    id: int
    customer_name: str
    customer_email: str
    feedback_text: str
    sentiment: Optional[str] = None
    category: Optional[str] = None
    ai_response: Optional[str] = None
    created_at: datetime

    class Config:
        """Tells Pydantic this can come from database models"""
        from_attributes = True