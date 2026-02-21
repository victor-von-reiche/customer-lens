"""
Feedback API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.feedback import Feedback
from app.api.schemas import FeedbackCreate, FeedbackResponse
from app.services.chatgpt_sentiment import analyze_sentiment  # NEW!

# Create a router - think of this as a section of the menu
router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new feedback entry with automatic sentiment analysis.

    This endpoint:
    1. Receives customer feedback
    2. Analyzes sentiment using ChatGPT
    3. Stores everything in database
    """

    # Step 1: Analyze sentiment using ChatGPT
    print(f" Analyzing sentiment for: {feedback.feedback_text[:50]}...")
    sentiment_result = await analyze_sentiment(feedback.feedback_text)
    print(f" Sentiment: {sentiment_result['sentiment']}")

    # Step 2: Create a new Feedback object with the sentiment
    db_feedback = Feedback(
        customer_name=feedback.customer_name,
        customer_email=feedback.customer_email,
        feedback_text=feedback.feedback_text,
        sentiment=sentiment_result['sentiment']  # Store the sentiment!
    )

    # Step 3: Add to database and commit (save)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)  # Get the ID that was auto-generated

    print(f" Saved feedback #{db_feedback.id} with sentiment: {sentiment_result['sentiment']}")

    return db_feedback


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """
    Get feedback by ID.

    This endpoint retrieves a specific feedback entry.

    """
    # Query the database for feedback with this ID
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    # If not found, return 404 error
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback