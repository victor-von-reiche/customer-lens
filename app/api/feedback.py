"""
Feedback API endpoints
These are the "menu items" customers can order from our API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.feedback import Feedback
from app.api.schemas import FeedbackCreate, FeedbackResponse

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
    Create new feedback entry.

    This endpoint receives customer feedback and stores it in the database.

    Think of it like: Customer fills out a form → We save it to our filing cabinet
    """
    # Create a new Feedback object from the input data
    db_feedback = Feedback(
        customer_name=feedback.customer_name,
        customer_email=feedback.customer_email,
        feedback_text=feedback.feedback_text
    )

    # Add to database and commit (save)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)  # Get the ID that was auto-generated

    return db_feedback


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
        feedback_id: int,
        db: Session = Depends(get_db)
):
    """
    Get feedback by ID.

    This endpoint retrieves a specific feedback entry.

    Think of it like: "Show me file #5 from the filing cabinet"
    """
    # Query the database for feedback with this ID
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    # If not found, return 404 error
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback