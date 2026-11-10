"""Persistent tickets, analysis attempts, approvals, and escalations."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    """Return a naive UTC timestamp for SQLite compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


class Feedback(Base):
    """Represent one support ticket independently of the customer."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(254), nullable=False, index=True)
    feedback_text = Column(Text, nullable=False)
    sentiment = Column(String(20))
    category = Column(String(50))
    urgency = Column(String(20))
    ai_response = Column(Text)
    status = Column(String(30), nullable=False, default="open")
    analysis_status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    resolved_at = Column(DateTime)

    customer = relationship("Customer", back_populates="feedbacks")
    messages = relationship(
        "Message",
        back_populates="feedback",
        order_by="Message.id",
        cascade="all, delete-orphan",
    )
    analyses = relationship(
        "Analysis",
        order_by="Analysis.id",
        cascade="all, delete-orphan",
    )
    approvals = relationship(
        "Approval",
        order_by="Approval.id",
        cascade="all, delete-orphan",
    )
    escalations = relationship(
        "Escalation",
        order_by="Escalation.id",
        cascade="all, delete-orphan",
    )


class Analysis(Base):
    """Keep immutable results and retrieved evidence for each attempt."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    status = Column(String(20), nullable=False)
    mode = Column(String(10), nullable=False)
    model = Column(String(100), nullable=False)
    message = relationship("Message")
    prompt_version = Column(String(30), nullable=False, default="support-v2")
    result = Column(JSON)
    sources = Column(JSON, nullable=False, default=list)
    error = Column(Text)
    latency_ms = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Float)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Approval(Base):
    """Record a reviewed response and its original analysis."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), unique=True)
    analysis = relationship("Analysis")
    request_id = Column(String(36), nullable=False, unique=True)
    reviewer = Column(String(100), nullable=False)
    original_response = Column(Text, nullable=False)
    approved_response = Column(Text, nullable=False)
    edited = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Escalation(Base):
    """Persist an internal alert until a reviewer handles it."""

    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), unique=True)
    analysis = relationship("Analysis")
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="new")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    handled_at = Column(DateTime)
