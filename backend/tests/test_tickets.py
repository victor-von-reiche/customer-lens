"""Workflow regressions for ticket triage and reviewed replies."""

import asyncio
from uuid import uuid4

from app.api.schemas import Classification, FeedbackCreate
from app.models.customer import Customer
from app.services.classification import Usage
from app.services.dashboard import calculate_dashboard_stats
from app.services.rag_response import analyze_ticket
from app.services.tickets import create_ticket


def submit(
    client, text="My parcel has not arrived.", email="alex@example.com"
):
    """Submit a synthetic customer ticket."""
    response = client.post(
        "/feedback/",
        json={
            "customer_name": "Alex",
            "customer_email": email,
            "feedback_text": text,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def approval(ticket, **overrides):
    """Build a review request for the current draft."""
    return {
        "approved_response": ticket["ai_response"],
        "reviewer": "Reviewer",
        "analysis_id": ticket["analyses"][-1]["id"],
        "request_id": str(uuid4()),
        **overrides,
    }


def test_new_submission_is_a_separate_ticket(client):
    first = submit(client)
    second = submit(client, "I was charged twice.")
    assert first["id"] != second["id"]
    assert first["customer_id"] == second["customer_id"]
    assert len(first["messages"]) == 1
    assert second["category"] == "pricing"


def test_critical_feedback_creates_persisted_alert(client):
    ticket = submit(client, "My brakes failed and caused an accident.")
    assert ticket["urgency"] == "critical"
    assert ticket["analysis_status"] == "completed"
    assert ticket["analyses"][0]["mode"] == "demo"
    assert ticket["analyses"][0]["sources"]
    assert any(s["id"] == "safety" for s in ticket["analyses"][0]["sources"])
    alert = client.get("/feedback/escalations").json()[0]
    response = client.patch(
        f"/feedback/escalations/{alert['id']}",
        json={
            "status": "acknowledged",
        },
    )
    assert response.json()["status"] == "acknowledged"
    assert response.json()["handled_at"].endswith("+00:00")


def test_approval_is_audited_and_idempotent(client):
    ticket = submit(client)
    payload = approval(ticket, approved_response="Reviewed and edited reply.")
    url = f"/feedback/{ticket['id']}/approve-and-send"
    first = client.post(url, json=payload)
    assert first.status_code == 200, first.text
    second = client.post(url, json=payload).json()
    assert second["status"] == "waiting_for_customer"
    assert len(second["approvals"]) == 1
    assert len(second["messages"]) == 2
    audit = second["approvals"][0]
    assert audit["edited"] is True
    assert audit["original_response"] == ticket["ai_response"]
    assert audit["approved_response"] == payload["approved_response"]
    assert client.post(url, json=approval(ticket)).status_code == 409


def test_stale_draft_is_rejected_and_followup_reopens_ticket(client):
    ticket = submit(client)
    old_approval = approval(ticket)
    client.patch(
        f"/feedback/{ticket['id']}/status", json={"status": "resolved"}
    )
    response = client.post(
        f"/feedback/{ticket['id']}/message",
        json={
            "content": "The parcel arrived. Thank you!",
            "sender": "customer",
        },
    )
    updated = response.json()
    assert updated["status"] == "open"
    assert updated["resolved_at"] is None
    assert len(updated["analyses"]) == 2
    assert (
        client.post(
            f"/feedback/{ticket['id']}/approve-and-send", json=old_approval
        ).status_code
        == 409
    )


def test_reply_does_not_resolve_ticket_or_alert(client):
    ticket = submit(client, "My brakes failed.")
    client.post(
        f"/feedback/{ticket['id']}/approve-and-send", json=approval(ticket)
    )
    stats = client.get("/feedback/stats").json()
    assert stats["waiting_count"] == 1
    assert stats["resolved_count"] == 0
    assert stats["active_escalations"] == 1
    client.patch(
        f"/feedback/{ticket['id']}/status", json={"status": "resolved"}
    )
    assert client.get("/feedback/stats").json()["resolved_count"] == 1


def test_blank_inputs_invalid_filters_and_sender_are_rejected(client):
    response = client.post(
        "/feedback/",
        json={
            "customer_name": "   ",
            "customer_email": "not-email",
            "feedback_text": " ",
        },
    )
    assert response.status_code == 422
    assert client.get("/feedback/?limit=-1").status_code == 422
    assert client.get("/feedback/?sort_by=unknown").status_code == 422
    ticket = submit(client)
    assert (
        client.post(
            f"/feedback/{ticket['id']}/message",
            json={
                "sender": "agent",
                "content": "Bypass approval",
            },
        ).status_code
        == 422
    )
    assert client.get("/feedback/99999").status_code == 404


def test_ticket_delete_removes_dependents_but_keeps_customer(client, db):
    ticket = submit(client, "My brakes failed.")
    client.post(
        f"/feedback/{ticket['id']}/approve-and-send", json=approval(ticket)
    )
    response = client.delete(f"/feedback/{ticket['id']}")
    assert response.status_code == 204, response.text
    assert client.get("/feedback/escalations").json() == []
    assert db.query(Customer).one().feedback_count == 0


def test_failed_analysis_never_becomes_low_urgency(db):
    class FailingProvider:
        model = "test-failure"

        async def classify(self, text, history=None):
            raise RuntimeError("Private provider error and secret")

    ticket = create_ticket(
        db,
        FeedbackCreate(
            customer_name="Alex",
            customer_email="alex@example.com",
            feedback_text="My brakes failed.",
        ),
    )
    asyncio.run(analyze_ticket(db, ticket, provider=FailingProvider()))
    assert ticket.analysis_status == "failed"
    assert ticket.urgency is ticket.sentiment is ticket.category is None
    assert ticket.ai_response is None
    assert "secret" not in ticket.analyses[-1].error
    assert ticket.escalations[-1].status == "new"
    assert calculate_dashboard_stats(db)["positive_sentiment_percent"] is None
    asyncio.run(analyze_ticket(db, ticket))
    assert ticket.analysis_status == "completed"
    assert len(ticket.analyses) == 2
    assert ticket.analyses[0].status == "failed"


def test_unknown_source_citation_fails_safely(db):
    from app.api.schemas import Draft

    class InvalidProvider:
        model = "test-invalid-source"

        async def classify(self, text, history=None):
            return Classification(
                sentiment="negative",
                category="product",
                urgency="high",
                explanation="Defect.",
            ), Usage()

        async def draft(self, *args):
            return Draft(
                response="A refund is guaranteed.",
                cited_source_ids=["invented-policy"],
                needs_review=True,
            ), Usage()

    ticket = create_ticket(
        db,
        FeedbackCreate(
            customer_name="Alex",
            customer_email="alex@example.com",
            feedback_text="My bike is broken.",
        ),
    )
    asyncio.run(analyze_ticket(db, ticket, provider=InvalidProvider()))
    assert ticket.analysis_status == "partial"
    assert ticket.sentiment == "negative"
    assert ticket.category == "product"
    assert ticket.urgency == "high"
    assert ticket.ai_response is None
    assert ticket.analyses[-1].result["category"] == "product"


def test_sentiment_denominator_excludes_failed_or_pending(db):
    for text in ["Excellent bike!", "Delivery was late."]:
        ticket = create_ticket(
            db,
            FeedbackCreate(
                customer_name="Alex",
                customer_email="alex@example.com",
                feedback_text=text,
            ),
        )
        asyncio.run(analyze_ticket(db, ticket))
    create_ticket(
        db,
        FeedbackCreate(
            customer_name="Alex",
            customer_email="alex@example.com",
            feedback_text="Unprocessed",
        ),
    )
    stats = calculate_dashboard_stats(db)
    assert stats["positive_sentiment_percent"] == 50
    assert stats["analyzed_count"] == 2
    assert stats["total_count"] == 3


def test_optional_api_token_and_rate_limit(client, monkeypatch):
    from dataclasses import replace

    import app.main as main

    monkeypatch.setattr(
        main, "settings", replace(main.settings, admin_token="test-token")
    )
    assert client.get("/feedback/").status_code == 401
    assert client.get("/config").json()["requires_token"] is True
    assert (
        client.get(
            "/feedback/",
            headers={
                "Authorization": "Bearer test-token",
            },
        ).status_code
        == 200
    )
    monkeypatch.setattr(
        main, "settings", replace(main.settings, admin_token="")
    )
    for _ in range(20):
        client.post("/feedback/99999/analyze")
    assert client.post("/feedback/99999/analyze").status_code == 429


def test_original_dashboard_sort_options(client):
    submit(client, "Excellent bike.")
    submit(client, "Delivery was late.")
    by_sentiment = client.get("/feedback/?sort_by=sentiment").json()
    assert [ticket["sentiment"] for ticket in by_sentiment] == [
        "negative",
        "positive",
    ]
    by_category = client.get("/feedback/?sort_by=category").json()
    assert [ticket["category"] for ticket in by_category] == [
        "delivery",
        "product",
    ]


def test_daily_gauge_metrics_come_from_backend(client):
    submit(client, "Excellent bike.")
    submit(client, "My brakes failed.")
    stats = client.get("/feedback/stats").json()
    assert stats["positive_today"] == 1
    assert stats["critical_today"] == 1
    assert stats["critical_resolved_today"] == 0
    assert stats["positive_sentiment_today_percent"] == 50


def test_gauge_preserves_saved_legacy_sentiment_and_excludes_unknown(db):
    for sentiment in ["positive", "mixed", "negative", None]:
        ticket = create_ticket(
            db,
            FeedbackCreate(
                customer_name="Legacy customer",
                customer_email="legacy@example.com",
                feedback_text="Saved entry",
            ),
        )
        ticket.sentiment = sentiment
    db.commit()
    stats = calculate_dashboard_stats(db)
    assert stats["non_negative_sentiment_percent"] == 67
    assert stats["positive_sentiment_percent"] == 33
    assert stats["analyzed_count"] == 3


def test_draft_failure_preserves_classification_and_critical_alert(db):
    class DraftFailureProvider:
        model = "test-draft-failure"

        async def classify(self, text, history=None):
            return Classification(
                sentiment="negative",
                category="product",
                urgency="critical",
                explanation="Brake failure.",
            ), Usage(input_tokens=30, output_tokens=10)

        async def draft(self, *args):
            raise RuntimeError("Draft unavailable")

    ticket = create_ticket(
        db,
        FeedbackCreate(
            customer_name="Customer",
            customer_email="customer@example.com",
            feedback_text="My brakes failed.",
        ),
    )
    asyncio.run(analyze_ticket(db, ticket, provider=DraftFailureProvider()))
    assert ticket.analysis_status == "partial"
    assert ticket.sentiment == "negative"
    assert ticket.category == "product"
    assert ticket.urgency == "critical"
    assert ticket.ai_response is None
    assert ticket.analyses[-1].result["category"] == "product"
    assert ticket.escalations[-1].status == "new"
    assert calculate_dashboard_stats(db)["analyzed_count"] == 1


def test_followup_classification_receives_only_its_ticket_history(db):
    from app.services.classification import DemoProvider
    from app.services.tickets import add_customer_message

    class RecordingProvider(DemoProvider):
        received_history = None

        async def classify(self, text, history=None):
            self.received_history = history
            return await super().classify(text, history)

    unrelated = create_ticket(
        db,
        FeedbackCreate(
            customer_name="Other",
            customer_email="other@example.com",
            feedback_text="Private unrelated message",
        ),
    )
    ticket = create_ticket(
        db,
        FeedbackCreate(
            customer_name="Customer",
            customer_email="customer@example.com",
            feedback_text="My parcel has not arrived.",
        ),
    )
    add_customer_message(db, ticket, "It is still missing.")
    provider = RecordingProvider()
    asyncio.run(analyze_ticket(db, ticket, provider=provider))
    assert provider.received_history == [
        {
            "sender": "customer",
            "content": "My parcel has not arrived.",
        }
    ]
    assert unrelated.feedback_text not in str(provider.received_history)


def test_screenshot_example_in_demo_is_positive_service():
    from app.services.classification import DemoProvider

    result, _ = asyncio.run(
        DemoProvider().classify(
            "One of the best stores ever!",
        )
    )
    assert result.sentiment == "positive"
    assert result.category == "service"
    assert result.urgency == "low"


def test_ticket_pages_keep_order_and_status_filters(client, db):
    from datetime import UTC, datetime, timedelta

    from app.models.feedback import Feedback

    customer = Customer(name="Page test", email="pages@example.com")
    db.add(customer)
    db.flush()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    tickets = [
        Feedback(
            customer_id=customer.id,
            customer_name=customer.name,
            customer_email=customer.email,
            feedback_text=f"Synthetic ticket {index}",
            created_at=start + timedelta(minutes=index),
            sentiment="negative",
            urgency="critical" if index == 0 else "low",
            category="product",
            analysis_status="completed",
            status="open" if index < 60 else "resolved",
        )
        for index in range(61)
    ]
    db.add_all(tickets)
    db.commit()
    first = client.get("/feedback/?status=open&sort_by=newest&limit=51").json()
    second = client.get(
        "/feedback/?status=open&sort_by=newest&skip=50&limit=51"
    ).json()
    assert len(first) == 51
    assert len(second) == 10
    visible_ids = [ticket["id"] for ticket in first[:50] + second]
    assert visible_ids == [ticket.id for ticket in reversed(tickets[:60])]
    assert (
        client.get("/feedback/?status=all&sort_by=newest&limit=1").json()[0][
            "id"
        ]
        == tickets[-1].id
    )
    assert (
        client.get("/feedback/?status=open&sort_by=urgency&limit=1").json()[0][
            "id"
        ]
        == tickets[0].id
    )
    assert (
        client.get(f"/feedback/{tickets[-1].id}").json()["status"]
        == "resolved"
    )
