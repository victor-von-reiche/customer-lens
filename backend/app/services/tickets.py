"""Ticket creation, reply review, and explicit lifecycle changes."""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.models.customer import Customer
from app.models.feedback import Approval, Feedback, utcnow
from app.models.message import Message


def find_ticket(db, ticket_id):
    """Find a ticket or return the API's not-found response."""
    ticket = db.get(Feedback, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    return ticket


def create_ticket(db, data):
    """Create an independent ticket and its first message atomically."""
    email = str(data.customer_email).lower()
    customer = (
        db.query(Customer).filter(func.lower(Customer.email) == email).first()
    )
    if customer is None:
        customer = Customer(email=email, name=data.customer_name)
        db.add(customer)
        db.flush()
    customer.last_contact = utcnow()
    customer.feedback_count = (
        db.query(Feedback).filter(Feedback.customer_id == customer.id).count()
        + 1
    )
    ticket = Feedback(
        customer_id=customer.id,
        customer_name=data.customer_name,
        customer_email=email,
        feedback_text=data.feedback_text,
    )
    ticket.messages.append(
        Message(sender="customer", content=data.feedback_text)
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def add_customer_message(db, ticket, content):
    """Append to an explicit ticket and reopen it for review."""
    if ticket.analysis_status == "processing":
        raise HTTPException(409, "An analysis is already running")
    ticket.messages.append(Message(sender="customer", content=content))
    ticket.feedback_text = content
    ticket.status = "open"
    ticket.resolved_at = None
    ticket.updated_at = utcnow()
    ticket.analysis_status = "pending"
    ticket.ai_response = None
    ticket.sentiment = ticket.category = ticket.urgency = None
    db.commit()
    db.refresh(ticket)
    return ticket


def approve_reply(db, ticket, data):
    """Record one reviewed reply with idempotency and stale-draft checks."""
    previous = (
        db.query(Approval).filter_by(request_id=str(data.request_id)).first()
    )
    if previous:
        if (
            previous.feedback_id != ticket.id
            or previous.approved_response != data.approved_response
            or previous.reviewer != data.reviewer
            or previous.analysis_id != data.analysis_id
        ):
            raise HTTPException(
                409, "Request ID was used for another approval"
            )
        return ticket
    if ticket.status == "resolved":
        raise HTTPException(409, "Reopen this ticket before replying")
    if ticket.analysis_status == "processing":
        raise HTTPException(409, "Wait for the current analysis to finish")
    original = ""
    if data.analysis_id is not None:
        analysis = next(
            (a for a in ticket.analyses if a.id == data.analysis_id), None
        )
        latest_customer = [
            m for m in ticket.messages if m.sender == "customer"
        ][-1]
        if (
            analysis is None
            or analysis.status != "completed"
            or analysis.message_id != latest_customer.id
            or analysis.id != ticket.analyses[-1].id
        ):
            raise HTTPException(409, "This draft is stale; refresh the ticket")
        if db.query(Approval).filter_by(analysis_id=analysis.id).first():
            raise HTTPException(409, "This draft was already approved")
        original = analysis.result["response"]
    ticket.approvals.append(
        Approval(
            analysis_id=data.analysis_id,
            request_id=str(data.request_id),
            reviewer=data.reviewer,
            original_response=original,
            approved_response=data.approved_response,
            edited=data.approved_response != original,
        )
    )
    ticket.messages.append(
        Message(sender="agent", content=data.approved_response)
    )
    ticket.status = "waiting_for_customer"
    ticket.updated_at = utcnow()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This reply was already approved") from None
    db.refresh(ticket)
    return ticket


def set_status(db, ticket, status):
    """Change ticket state without inferring resolution from a reply."""
    if ticket.analysis_status == "processing":
        raise HTTPException(409, "Wait for the current analysis to finish")
    ticket.status = status
    ticket.updated_at = utcnow()
    ticket.resolved_at = utcnow() if status == "resolved" else None
    db.commit()
    db.refresh(ticket)
    return ticket
