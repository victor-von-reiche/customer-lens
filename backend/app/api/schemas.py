"""Validated API inputs and outputs."""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    StringConstraints,
    field_serializer,
)

ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10000),
]
TicketStatus = Literal["open", "waiting_for_customer", "resolved"]


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", check_fields=False)
    def serialize_dates(self, value):
        """Expose legacy naive timestamps explicitly as UTC."""
        if isinstance(value, datetime):
            return value.replace(tzinfo=UTC).isoformat()
        return value


class FeedbackCreate(BaseModel):
    customer_name: ShortText
    customer_email: EmailStr
    feedback_text: MessageText


class MessageCreate(BaseModel):
    sender: Literal["customer"] = "customer"
    content: MessageText


class StatusUpdate(BaseModel):
    status: TicketStatus


class ApprovalCreate(BaseModel):
    approved_response: MessageText
    reviewer: ShortText
    analysis_id: int | None = None
    request_id: UUID


class EscalationUpdate(BaseModel):
    status: Literal["acknowledged", "resolved"]


class Source(BaseModel):
    id: str
    title: str
    version: str
    text: str
    score: float


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    category: Literal["product", "service", "delivery", "pricing"]
    urgency: Literal["critical", "high", "medium", "low"]
    explanation: str


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    cited_source_ids: list[str]
    needs_review: bool


class AnalysisResponse(ORMResponse):
    id: int
    message_id: int
    status: str
    mode: str
    model: str
    prompt_version: str
    result: dict | None
    sources: list[Source]
    error: str | None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    created_at: datetime


class MessageResponse(ORMResponse):
    id: int
    feedback_id: int
    sender: str
    content: str
    timestamp: datetime


class ApprovalResponse(ORMResponse):
    id: int
    analysis_id: int | None
    reviewer: str
    original_response: str
    approved_response: str
    edited: bool
    created_at: datetime


class EscalationResponse(ORMResponse):
    id: int
    feedback_id: int
    analysis_id: int | None
    reason: str
    status: str
    created_at: datetime
    handled_at: datetime | None


class FeedbackResponse(ORMResponse):
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    feedback_text: str
    sentiment: str | None
    category: str | None
    urgency: str | None
    ai_response: str | None
    status: TicketStatus
    analysis_status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    messages: list[MessageResponse]
    analyses: list[AnalysisResponse]
    approvals: list[ApprovalResponse]
    escalations: list[EscalationResponse]


class DashboardStatsResponse(BaseModel):
    non_negative_sentiment_percent: int | None
    non_negative_sentiment_today_percent: int | None
    critical_today: int
    critical_resolved_today: int
    positive_today: int
    positive_sentiment_today_percent: int | None
    total_count: int
    open_count: int
    waiting_count: int
    resolved_count: int
    positive_sentiment_percent: int | None
    analyzed_count: int
    failed_count: int
    active_escalations: int
    created_today: int
    resolved_today: int
