"""Dashboard metrics with explicit status and sentiment definitions."""

from datetime import UTC, datetime

from sqlalchemy import func

from app.models.feedback import Escalation, Feedback


def calculate_dashboard_stats(db):
    """Count states and sentiment, including saved legacy classifications."""
    tickets = db.query(Feedback).all()
    analyzed = [
        t
        for t in tickets
        if t.analysis_status in {"completed", "partial"}
        or (
            t.analysis_status == "pending"
            and not t.analyses
            and t.sentiment in {"positive", "negative", "neutral", "mixed"}
        )
    ]
    today = datetime.now(UTC).date()
    analyzed_today = [t for t in analyzed if t.created_at.date() == today]
    critical_today = [t for t in analyzed_today if t.urgency == "critical"]
    return {
        "non_negative_sentiment_percent": round(
            sum(t.sentiment != "negative" for t in analyzed)
            / len(analyzed)
            * 100
        )
        if analyzed
        else None,
        "non_negative_sentiment_today_percent": round(
            sum(t.sentiment != "negative" for t in analyzed_today)
            / len(analyzed_today)
            * 100
        )
        if analyzed_today
        else None,
        "critical_today": len(critical_today),
        "critical_resolved_today": sum(
            t.status == "resolved" for t in critical_today
        ),
        "positive_today": sum(
            t.sentiment == "positive" for t in analyzed_today
        ),
        "positive_sentiment_today_percent": round(
            sum(t.sentiment == "positive" for t in analyzed_today)
            / len(analyzed_today)
            * 100
        )
        if analyzed_today
        else None,
        "total_count": len(tickets),
        "open_count": sum(t.status == "open" for t in tickets),
        "waiting_count": sum(
            t.status == "waiting_for_customer" for t in tickets
        ),
        "resolved_count": sum(t.status == "resolved" for t in tickets),
        "positive_sentiment_percent": round(
            sum(t.sentiment == "positive" for t in analyzed)
            / len(analyzed)
            * 100
        )
        if analyzed
        else None,
        "analyzed_count": len(analyzed),
        "failed_count": sum(t.analysis_status == "failed" for t in tickets),
        "active_escalations": db.query(Escalation)
        .filter(Escalation.status != "resolved")
        .count(),
        "created_today": sum(t.created_at.date() == today for t in tickets),
        "resolved_today": sum(
            t.resolved_at is not None and t.resolved_at.date() == today
            for t in tickets
        ),
    }


def get_filtered_sorted_feedbacks(db, sentiment, status, sort_by, skip, limit):
    """Filter and paginate in SQL with a stable ticket-ID tie breaker."""
    from sqlalchemy import case

    query = db.query(Feedback)
    if sentiment != "all":
        query = query.filter(func.lower(Feedback.sentiment) == sentiment)
    if status != "all":
        query = query.filter(Feedback.status == status)
    priority = case(
        (Feedback.analysis_status == "failed", 0),
        (Feedback.urgency == "critical", 1),
        (Feedback.urgency == "high", 2),
        (Feedback.urgency == "medium", 3),
        else_=4,
    )
    ordering = {
        "urgency": [priority, Feedback.updated_at.desc()],
        "newest": [Feedback.created_at.desc()],
        "oldest": [Feedback.created_at.asc()],
        "sentiment": [
            case(
                (Feedback.sentiment == "negative", 0),
                (Feedback.sentiment == "mixed", 1),
                (Feedback.sentiment == "neutral", 2),
                else_=3,
            ),
            Feedback.updated_at.desc(),
        ],
        "category": [Feedback.category.asc()],
    }
    return (
        query.order_by(*ordering[sort_by], Feedback.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
