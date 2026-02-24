from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.feedback import Feedback
from app.api.schemas import FeedbackCreate, FeedbackResponse
from app.services.chatgpt_sentiment import analyze_sentiment
from app.services.gemini_category import categorize_feedback  # NEW!

# Create a router
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
    Create new feedback entry with AI analysis.

    This endpoint:
    1. Receives customer feedback
    2. Analyzes sentiment using ChatGPT
    3. Categorizes using Gemini
    4. Stores everything in database
    """

    print(f"\n{'='*60}")
    print(f"New feedback from: {feedback.customer_name}")
    print(f"Feedback: {feedback.feedback_text[:80]}...")
    print(f"{'='*60}")

    # Step 1: Analyze sentiment using ChatGPT
    print("ChatGPT analyzing sentiment...")
    sentiment_result = await analyze_sentiment(feedback.feedback_text)
    print(f"Sentiment: {sentiment_result['sentiment']}")

    # Step 2: Categorize using Gemini (NEW!)
    print("Gemini categorizing feedback...")
    category_result = await categorize_feedback(feedback.feedback_text)
    print(f"Category: {category_result['category']}")

    # Step 3: Create feedback entry with BOTH results
    db_feedback = Feedback(
        customer_name=feedback.customer_name,
        customer_email=feedback.customer_email,
        feedback_text=feedback.feedback_text,
        sentiment=sentiment_result['sentiment'],
        category=category_result['category']
    )

    # Step 4: Save to database
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    print(f"Saved as feedback #{db_feedback.id}")
    print(f"{'='*60}\n")

    return db_feedback


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """
    Get feedback by ID.
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback