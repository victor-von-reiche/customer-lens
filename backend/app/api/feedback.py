"""
Feedback API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import os
import httpx

from app.database.db import get_db
from app.models.feedback import Feedback
from app.models.customer import Customer
from app.models.message import Message
from app.api.schemas import FeedbackCreate, FeedbackResponse, FeedbackUpdate, MessageCreate, DashboardStatsResponse
from app.services.chatgpt_sentiment import analyze_sentiment
from app.services.gemini_category import categorize_feedback
from app.services.rag_response import generate_response
from app.services.dashboard import calculate_dashboard_stats, get_filtered_sorted_feedbacks

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)


def get_or_create_customer(db: Session, email: str, name: str) -> Customer:
    """
    Get existing customer or create new one.

    Args:
        db: Database session
        email: Customer email
        name: Customer name

    Returns:
        Customer object
    """
    customer = db.query(Customer).filter(Customer.email == email).first()

    if customer:
        customer.feedback_count += 1
        customer.name = name
        print(f"Existing customer: {customer.email} (total feedback: {customer.feedback_count})")
    else:
        customer = Customer(
            email=email,
            name=name,
            feedback_count=1
        )
        db.add(customer)
        print(f"New customer: {customer.email}")

    db.commit()
    db.refresh(customer)
    return customer


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
        feedback: FeedbackCreate,
        db: Session = Depends(get_db)
):
    """
    Create new feedback with complete AI analysis.

    If a feedback thread already exists for this customer email,
    the new message is appended to the existing conversation and
    AI analysis is re-run on the latest message.
    """

    print(f"\n{'=' * 60}")
    print(f"New feedback from: {feedback.customer_name}")
    print(f"Feedback: {feedback.feedback_text[:80]}...")
    print(f"{'=' * 60}")

    customer = get_or_create_customer(db, feedback.customer_email, feedback.customer_name)

    print("Analyzing sentiment...")
    sentiment_result = await analyze_sentiment(feedback.feedback_text)
    print(f"Sentiment: {sentiment_result['sentiment']}")

    print("Categorizing feedback...")
    category_result = await categorize_feedback(feedback.feedback_text)
    print(f"Category: {category_result['category']}, Urgency: {category_result['urgency']}")

    existing_feedback = (
        db.query(Feedback)
        .filter(Feedback.customer_email == feedback.customer_email)
        .order_by(Feedback.created_at.desc())
        .first()
    )

    if existing_feedback:
        conversation_history = "\n".join(
            f"[{msg.sender.upper()}]: {msg.content}"
            for msg in existing_feedback.messages
        )

        print("Generating response with full conversation context...")
        response_result = await generate_response(
            feedback.feedback_text,
            sentiment_result['sentiment'],
            category_result['category'],
            conversation_history=conversation_history
        )
        print(f"Response generated with conversation context")

        existing_feedback.sentiment = sentiment_result['sentiment']
        existing_feedback.category = category_result['category']
        existing_feedback.urgency = category_result['urgency']
        existing_feedback.ai_response = response_result['response']
        existing_feedback.feedback_text = feedback.feedback_text

        new_message = Message(
            feedback_id=existing_feedback.id,
            sender='customer',
            content=feedback.feedback_text
        )
        db.add(new_message)
        db.commit()
        db.refresh(existing_feedback)

        if existing_feedback.urgency == "critical":
            await trigger_n8n_webhook(existing_feedback)

        print(f"Appended to existing feedback #{existing_feedback.id} for customer #{customer.id}")
        print(f"{'=' * 60}\n")

        return existing_feedback

    print("Generating response with company guidelines...")
    response_result = await generate_response(
        feedback.feedback_text,
        sentiment_result['sentiment'],
        category_result['category']
    )
    print(f"Response generated")

    db_feedback = Feedback(
        customer_id=customer.id,
        customer_name=feedback.customer_name,
        customer_email=feedback.customer_email,
        feedback_text=feedback.feedback_text,
        sentiment=sentiment_result['sentiment'],
        category=category_result['category'],
        urgency=category_result['urgency'],
        ai_response=response_result['response']
    )

    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    initial_message = Message(
        feedback_id=db_feedback.id,
        sender='customer',
        content=feedback.feedback_text
    )
    db.add(initial_message)
    db.commit()
    db.refresh(db_feedback)

    if db_feedback.urgency == "critical":
        await trigger_n8n_webhook(db_feedback)

    print(f"Saved as feedback #{db_feedback.id} for customer #{customer.id}")
    print(f"{'=' * 60}\n")

    return db_feedback


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats_endpoint(
        db: Session = Depends(get_db)
):
    """Get calculated dashboard statistics."""
    stats = calculate_dashboard_stats(db)
    return stats


@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
        filter: str = 'All',
        sort_by: str = 'Urgency',
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """List all feedback entries (for dashboard) with filtering and sorting."""
    feedbacks = get_filtered_sorted_feedbacks(db, filter, sort_by, skip, limit)
    return feedbacks


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
        feedback_id: int,
        db: Session = Depends(get_db)
):
    """Get feedback by ID."""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
        feedback_id: int,
        feedback_in: FeedbackUpdate,
        db: Session = Depends(get_db)
):
    """Update feedback (e.g., for AI response approval)."""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    update_data = feedback_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_feedback, key, value)

    db.commit()
    db.refresh(db_feedback)
    return db_feedback


@router.post("/{feedback_id}/approve-and-send")

async def approve_and_send_feedback(

    feedback_id: int,

    approved_response: str = Body(None),

    db: Session = Depends(get_db)

):
    """
    Approve a generated AI response and automatically add it to the
    existing frontend chat thread as an agent message.
    """
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    if not db_feedback.ai_response:
        raise HTTPException(status_code=400, detail="No AI response available")

    final_response = approved_response or db_feedback.ai_response

    existing_agent_message = (
        db.query(Message)
        .filter(
            Message.feedback_id == feedback_id,
            Message.sender == 'agent',
            Message.content == final_response
        )
        .first()
    )

    if existing_agent_message:
        print(f"AI response for feedback #{feedback_id} was already added to the chat")
        db.refresh(db_feedback)
        return db_feedback

    db_feedback.ai_response = final_response

    approved_message = Message(
        feedback_id=feedback_id,
        sender='agent',
        content=final_response
    )
    db.add(approved_message)
    db.commit()
    db.refresh(db_feedback)

    print(f"Approved AI response added to chat for feedback #{feedback_id}")
    return db_feedback


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(
        feedback_id: int,
        db: Session = Depends(get_db)
):
    """Delete a feedback entry."""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Update customer feedback count
    customer = db_feedback.customer
    if customer:
        customer.feedback_count = max(0, customer.feedback_count - 1)
        if customer.feedback_count == 0:
            print(f"Deleting customer {customer.email} as they have no more feedback")
            db.delete(customer)
        else:
            print(f"Updated customer {customer.email} feedback count to {customer.feedback_count}")

    db.delete(db_feedback)
    db.commit()
    return None


@router.get("/customer/{email}", response_model=List[FeedbackResponse])
async def get_customer_feedback(
        email: str,
        db: Session = Depends(get_db)
):
    """Get all feedback from a specific customer by email."""
    customer = db.query(Customer).filter(Customer.email == email).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    feedbacks = db.query(Feedback).filter(Feedback.customer_id == customer.id).all()

    return feedbacks


@router.post("/{feedback_id}/message", response_model=FeedbackResponse)
async def add_message(
    feedback_id: int,
    message_in: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a new message to a feedback thread."""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    new_message = Message(
        feedback_id=feedback_id,
        sender=message_in.sender,
        content=message_in.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


async def trigger_n8n_webhook(feedback: Feedback) -> None:
    """
    Send critical feedback data to an n8n webhook.

    Args:
        feedback: The saved feedback object that should be forwarded to n8n.

    Returns:
        None
    """
    webhook_url = os.getenv("N8N_CRITICAL_FEEDBACK_WEBHOOK")

    if not webhook_url:
        print("N8N webhook URL not configured")
        return

    payload = {
        "feedback_id": feedback.id,
        "customer_name": feedback.customer_name,
        "customer_email": feedback.customer_email,
        "feedback_text": feedback.feedback_text,
        "sentiment": feedback.sentiment,
        "category": feedback.category,
        "urgency": feedback.urgency,
        "ai_response": feedback.ai_response,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"Critical feedback #{feedback.id} sent to n8n")

    except Exception as e:
        print(f"Error sending webhook to n8n: {e}")