"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class FeedbackCreate(BaseModel):
    """Schema for creating new feedback."""
    customer_name: str
    customer_email: EmailStr
    feedback_text: str


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    sender: str  # 'customer', 'agent', 'system'
    content: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    feedback_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """Schema for feedback responses."""
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    feedback_text: str
    sentiment: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    ai_response: Optional[str] = None
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class FeedbackUpdate(BaseModel):
    """Schema for updating an existing feedback entry."""
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    feedback_text: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    ai_response: Optional[str] = None


class DashboardStatsResponse(BaseModel):
    """Schema for dashboard overall statistics."""
    total_count: int
    open_count: int
    closed_count: int
    satisfaction_score: int
    processed_today: int
    critical_today: int
    critical_resolved_today: int
    positive_today: int
    satisfaction_today: int