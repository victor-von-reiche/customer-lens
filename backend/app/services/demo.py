"""Synthetic demo tickets for a useful first launch."""

from app.api.schemas import ApprovalCreate, FeedbackCreate
from app.models.feedback import Feedback
from app.services.rag_response import analyze_ticket
from app.services.tickets import approve_reply, create_ticket, set_status

SAMPLES = [
    ("Alex Morgan", "My brakes failed and caused an accident. I need help."),
    ("Sam Rivera", "My parcel has not arrived and the tracking is missing."),
    ("Taylor Reed", "I love my new bike, but the delivery was late."),
    ("Jordan Kim", "The bike quality is excellent. Thank you!"),
    ("Casey Lee", "I was charged twice for my order."),
    ("Robin Chen", "Support was rude and I received no reply."),
]


async def seed_demo(db):
    """Seed examples only when the selected demo database is empty."""
    from uuid import uuid4

    if db.query(Feedback).count():
        return
    for index, (name, content) in enumerate(SAMPLES):
        ticket = create_ticket(
            db,
            FeedbackCreate(
                customer_name=name,
                customer_email=f"demo{index}@example.com",
                feedback_text=content,
            ),
        )
        await analyze_ticket(db, ticket)
        if index == 3:
            approve_reply(
                db,
                ticket,
                ApprovalCreate(
                    approved_response=ticket.ai_response,
                    reviewer="Demo reviewer",
                    analysis_id=ticket.analyses[-1].id,
                    request_id=uuid4(),
                ),
            )
            set_status(db, ticket, "resolved")
        elif index == 2:
            approve_reply(
                db,
                ticket,
                ApprovalCreate(
                    approved_response=ticket.ai_response,
                    reviewer="Demo reviewer",
                    analysis_id=ticket.analyses[-1].id,
                    request_id=uuid4(),
                ),
            )
