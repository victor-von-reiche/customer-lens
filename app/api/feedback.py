"""
Feedback API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.feedback import Feedback
from app.models.customer import Customer
from app.api.schemas import FeedbackCreate, FeedbackResponse
from app.services.chatgpt_sentiment import analyze_sentiment
from app.services.gemini_category import categorize_feedback
from app.services.rag_response import generate_response

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
    print(f"Category: {category_result['category']}")

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
        ai_response=response_result['response']
    )

    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    print(f"Saved as feedback #{db_feedback.id} for customer #{customer.id}")
    print(f"{'=' * 60}\n")

    return db_feedback


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