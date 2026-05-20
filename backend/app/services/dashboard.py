"""
Dashboard Service
Handles data processing logic for the CS dashboard, decoupling from the frontend.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.feedback import Feedback


def calculate_dashboard_stats(db: Session) -> dict:
    """
    Calculate KPIs for the dashboard based on stored feedback.

    Args:
        db: Database session

    Returns:
        dict: A dictionary of dashboard statistics metrics.
    """
    feedbacks = db.query(Feedback).all()
    total_count = len(feedbacks)

    open_count = 0
    closed_count = 0
    non_negative_count = 0

    today_date = datetime.utcnow().date()
    processed_today = 0
    critical_today = []
    positive_today = 0
    non_negative_today = 0

    for f in feedbacks:
        messages = f.messages
        if not messages or messages[-1].sender == 'customer':
            open_count += 1
        else:
            closed_count += 1

        sentiment_lower = (f.sentiment or "").lower()
        if sentiment_lower != 'negative':
            non_negative_count += 1

        f_date = f.created_at.date() if f.created_at else None
        if f_date == today_date:
            processed_today += 1
            if (f.urgency or "").lower() == 'critical':
                critical_today.append(f)
            if sentiment_lower == 'positive':
                positive_today += 1
            if sentiment_lower != 'negative':
                non_negative_today += 1

    satisfaction_score = round((non_negative_count / total_count) * 100) if total_count > 0 else 0
    satisfaction_today = round((non_negative_today / processed_today) * 100) if processed_today > 0 else 0

    critical_resolved_today = 0
    for cf in critical_today:
        c_msgs = cf.messages
        if c_msgs and c_msgs[-1].sender != 'customer':
            critical_resolved_today += 1

    return {
        "total_count": total_count,
        "open_count": open_count,
        "closed_count": closed_count,
        "satisfaction_score": satisfaction_score,
        "processed_today": processed_today,
        "critical_today": len(critical_today),
        "critical_resolved_today": critical_resolved_today,
        "positive_today": positive_today,
        "satisfaction_today": satisfaction_today
    }


def get_filtered_sorted_feedbacks(
    db: Session,
    filter_val: str,
    sort_by: str,
    skip: int = 0,
    limit: int = 100
) -> List[Feedback]:
    """
    Apply filtering and priority sorting on feedbacks.

    Args:
        db: Database session
        filter_val: The exact sentiment to filter by ('All', 'Positive', 'Negative', 'Mixed')
        sort_by: The sort order method
        skip: records to skip
        limit: items limit

    Returns:
        List[Feedback]: The sorted and filtered record set.
    """
    query = db.query(Feedback)

    if filter_val and filter_val.lower() != 'all':
        query = query.filter(func.lower(Feedback.sentiment) == filter_val.lower())

    feedbacks = query.all()

    def get_priority_score(item: Feedback) -> int:
        u = (item.urgency or "").lower()
        if u == 'critical':
            return 4
        if u == 'high':
            return 3
        if u == 'medium':
            return 2
        if u == 'low':
            return 1

        s = (item.sentiment or "").lower()
        if s == 'negative':
            return 3
        if s == 'mixed':
            return 2
        return 1

    def get_sentiment_score(item: Feedback) -> int:
        s = (item.sentiment or "").lower()
        if s == 'negative':
            return 3
        if s == 'mixed':
            return 2
        return 1

    def get_timestamp(item: Feedback) -> float:
        if not item.created_at:
            return 0.0
        return item.created_at.timestamp()

    if sort_by == 'Urgency':
        feedbacks.sort(
            key=lambda x: (-get_priority_score(x), -get_timestamp(x))
        )
    elif sort_by == 'Newest':
        feedbacks.sort(key=lambda x: -get_timestamp(x))
    elif sort_by == 'Oldest':
        feedbacks.sort(key=lambda x: get_timestamp(x))
    elif sort_by == 'Sentiment':
        feedbacks.sort(
            key=lambda x: (-get_sentiment_score(x), -get_timestamp(x))
        )
    elif sort_by == 'Category':
        feedbacks.sort(key=lambda x: x.category or "")

    return feedbacks[skip : skip + limit]
