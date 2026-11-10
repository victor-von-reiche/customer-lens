"""Ticket, analysis, approval, and escalation endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApprovalCreate,
    DashboardStatsResponse,
    EscalationResponse,
    EscalationUpdate,
    FeedbackCreate,
    FeedbackResponse,
    MessageCreate,
    StatusUpdate,
)
from app.database.db import get_db
from app.models.customer import Customer
from app.models.feedback import Escalation, Feedback, utcnow
from app.services.dashboard import (
    calculate_dashboard_stats,
    get_filtered_sorted_feedbacks,
)
from app.services.rag_response import analyze_ticket
from app.services.tickets import (
    add_customer_message,
    approve_reply,
    create_ticket,
    find_ticket,
    set_status,
)

router = APIRouter(prefix="/feedback", tags=["tickets"])


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    """Create a new ticket and attempt its initial analysis."""
    ticket = create_ticket(db, data)
    return await analyze_ticket(db, ticket)


@router.get("/stats", response_model=DashboardStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Return operational counts and the positive-sentiment share."""
    return calculate_dashboard_stats(db)


@router.get("/escalations", response_model=list[EscalationResponse])
def list_escalations(db: Session = Depends(get_db)):
    """List persisted alerts, including acknowledged and resolved alerts."""
    return db.query(Escalation).order_by(Escalation.id.desc()).limit(200).all()


@router.patch("/escalations/{alert_id}", response_model=EscalationResponse)
def update_escalation(
    alert_id: int, data: EscalationUpdate, db: Session = Depends(get_db)
):
    """Acknowledge or resolve an alert independently of the ticket."""
    alert = db.get(Escalation, alert_id)
    if alert is None:
        raise HTTPException(404, "Escalation not found")
    alert.status = data.status
    alert.handled_at = utcnow()
    db.commit()
    return alert


@router.get("/", response_model=list[FeedbackResponse])
def list_feedback(
    filter: Literal["all", "positive", "negative", "neutral", "mixed"] = "all",
    status: Literal["all", "open", "waiting_for_customer", "resolved"] = "all",
    sort_by: Literal[
        "urgency", "newest", "oldest", "sentiment", "category"
    ] = "urgency",
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List tickets with validated filters, ordering, and pagination."""
    return get_filtered_sorted_feedbacks(
        db, filter, status, sort_by, skip, limit
    )


@router.get("/customer/{email}", response_model=list[FeedbackResponse])
def customer_feedback(email: str, db: Session = Depends(get_db)):
    """Return independent tickets belonging to one customer."""
    customer = (
        db.query(Customer)
        .filter(func.lower(Customer.email) == email.lower())
        .first()
    )
    if customer is None:
        raise HTTPException(404, "Customer not found")
    return db.query(Feedback).filter_by(customer_id=customer.id).all()


@router.get("/{ticket_id}", response_model=FeedbackResponse)
def get_feedback(ticket_id: int, db: Session = Depends(get_db)):
    """Return one ticket with analysis evidence and approval history."""
    return find_ticket(db, ticket_id)


@router.patch("/{ticket_id}/status", response_model=FeedbackResponse)
def change_status(
    ticket_id: int, data: StatusUpdate, db: Session = Depends(get_db)
):
    """Set the ticket's explicit operational status."""
    return set_status(db, find_ticket(db, ticket_id), data.status)


@router.post("/{ticket_id}/analyze", response_model=FeedbackResponse)
async def retry_analysis(ticket_id: int, db: Session = Depends(get_db)):
    """Run a new analysis attempt while retaining earlier evidence."""
    ticket = find_ticket(db, ticket_id)
    if ticket.analysis_status == "processing":
        raise HTTPException(409, "An analysis is already running")
    if ticket.status == "resolved":
        raise HTTPException(409, "Reopen this ticket before analyzing")
    return await analyze_ticket(db, ticket)


@router.post("/{ticket_id}/message", response_model=FeedbackResponse)
async def append_message(
    ticket_id: int, data: MessageCreate, db: Session = Depends(get_db)
):
    """Append a customer follow-up to a specific ticket and reanalyze it."""
    ticket = add_customer_message(db, find_ticket(db, ticket_id), data.content)
    return await analyze_ticket(db, ticket)


@router.post("/{ticket_id}/approve-and-send", response_model=FeedbackResponse)
def approve_response(
    ticket_id: int, data: ApprovalCreate, db: Session = Depends(get_db)
):
    """Save a reviewed response to the conversation, without external email."""
    return approve_reply(db, find_ticket(db, ticket_id), data)


@router.delete("/{ticket_id}", status_code=204)
def delete_feedback(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket and its dependent records while keeping the customer."""
    ticket = find_ticket(db, ticket_id)
    if ticket.analysis_status == "processing":
        raise HTTPException(409, "Wait for the current analysis to finish")
    customer = ticket.customer
    db.delete(ticket)
    db.flush()
    customer.feedback_count = (
        db.query(Feedback).filter_by(customer_id=customer.id).count()
    )
    db.commit()
