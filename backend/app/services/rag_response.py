"""Run an analysis attempt and persist its evidence and outcome."""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from time import perf_counter

from app.config import BACKEND_DIR, settings
from app.models.feedback import Analysis, Escalation, utcnow
from app.rag.vectorstore import CompanyKnowledgeBase
from app.services.analysis_errors import describe_error
from app.services.classification import (
    PROMPT_VERSION,
    DemoProvider,
    LiveProvider,
)

logger = logging.getLogger(__name__)
log_path = BACKEND_DIR / "logs"
log_path.mkdir(exist_ok=True)
if not any(
    isinstance(handler, RotatingFileHandler) for handler in logger.handlers
):
    handler = RotatingFileHandler(
        log_path / "analysis.log", maxBytes=1_000_000, backupCount=3
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)

knowledge_base = CompanyKnowledgeBase(backend=settings.rag_backend)


def get_provider():
    """Use the live provider unless demo mode was explicitly selected."""
    if settings.mode == "demo":
        return DemoProvider()
    return LiveProvider(settings.gemini_api_key, settings.model)


def _save_completed_analysis(
    db, ticket, attempt, message_id, classification, draft
):
    """Apply a completed result only to the latest customer message."""
    db.refresh(ticket)
    latest = [m for m in ticket.messages if m.sender == "customer"][-1]
    if latest.id != message_id:
        attempt.status = "superseded"
    else:
        attempt.status = "completed"
        ticket.analysis_status = "completed"
        ticket.sentiment = classification.sentiment
        ticket.category = classification.category
        ticket.urgency = classification.urgency
        ticket.ai_response = draft.response
        if classification.urgency == "critical":
            db.add(
                Escalation(
                    feedback_id=ticket.id,
                    analysis_id=attempt.id,
                    reason=classification.explanation,
                )
            )


def _save_failed_analysis(
    db, ticket, attempt, message_id, classification, error
):
    """Retain valid labels and record a failed or superseded attempt."""
    issue = describe_error(error)
    logger.warning(
        "Analysis attempt %s ticket %s: %s (%s)",
        attempt.id,
        ticket.id,
        issue.code,
        type(error).__name__,
    )
    attempt.status = "partial" if classification else "failed"
    attempt.error = (
        "A reply could not be prepared. Please write a response or try again."
        if classification
        else "Please review this feedback or try again."
    )
    db.refresh(ticket)
    latest = [m for m in ticket.messages if m.sender == "customer"][-1]
    if latest.id == message_id:
        ticket.analysis_status = attempt.status
        ticket.ai_response = None
        if classification:
            ticket.sentiment = classification.sentiment
            ticket.category = classification.category
            ticket.urgency = classification.urgency
        else:
            ticket.sentiment = ticket.category = ticket.urgency = None
        if classification is None or classification.urgency == "critical":
            db.add(
                Escalation(
                    feedback_id=ticket.id,
                    analysis_id=attempt.id,
                    reason="This feedback needs your review.",
                )
            )
    else:
        attempt.status = "superseded"


async def analyze_ticket(db, ticket, provider=None, knowledge=None):
    """Store successful, failed, or superseded attempts without fake labels."""
    owns_provider = provider is None
    provider = provider or get_provider()
    knowledge = knowledge or knowledge_base
    message = next(
        message
        for message in reversed(ticket.messages)
        if message.sender == "customer"
    )
    attempt = Analysis(
        feedback_id=ticket.id,
        message_id=message.id,
        status="processing",
        mode=settings.mode,
        model=provider.model,
        prompt_version=PROMPT_VERSION,
        sources=[],
    )
    db.add(attempt)
    ticket.analysis_status = "processing"
    db.commit()
    started = perf_counter()
    classification = None
    history = [
        {"sender": item.sender, "content": item.content[-2000:]}
        for item in ticket.messages[-9:]
        if item.id != message.id
    ]
    try:
        classification, classification_usage = await provider.classify(
            message.content, history=history
        )
        attempt.result = classification.model_dump()
        attempt.input_tokens = classification_usage.input_tokens
        attempt.output_tokens = classification_usage.output_tokens
        query = f"{classification.category} {message.content}"
        if classification.urgency == "critical":
            query += " safety injury brake failure"
        elif classification.sentiment == "positive":
            query += " positive feedback"
        sources = await asyncio.to_thread(knowledge.search, query)
        attempt.sources = [source.model_dump() for source in sources]
        draft, draft_usage = await provider.draft(
            message.content, classification, sources, history
        )
        attempt.input_tokens += draft_usage.input_tokens
        attempt.output_tokens += draft_usage.output_tokens
        allowed = {source.id for source in sources}
        if not set(draft.cited_source_ids) <= allowed:
            raise ValueError("The draft referenced an unknown source")
        if not draft.response.strip():
            raise ValueError("The draft was empty")
        draft.needs_review = True
        attempt.result = {
            **classification.model_dump(),
            **draft.model_dump(),
        }
        _save_completed_analysis(
            db, ticket, attempt, message.id, classification, draft
        )
    except Exception as error:
        _save_failed_analysis(
            db, ticket, attempt, message.id, classification, error
        )
    finally:
        attempt.latency_ms = round((perf_counter() - started) * 1000)
        if settings.mode == "demo":
            attempt.estimated_cost_usd = 0
        if (
            settings.mode == "live"
            and settings.input_price is not None
            and settings.output_price is not None
        ):
            attempt.estimated_cost_usd = (
                attempt.input_tokens * settings.input_price
                + attempt.output_tokens * settings.output_price
            ) / 1_000_000
        ticket.updated_at = utcnow()
        db.commit()
        db.refresh(ticket)
        if owns_provider and isinstance(provider, LiveProvider):
            await provider.client.aclose()
    return ticket
