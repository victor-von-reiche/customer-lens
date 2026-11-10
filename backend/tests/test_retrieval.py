"""Policy reload and legacy storage regressions."""

import json
import sqlite3

from app.database.db import init_db
from app.rag.vectorstore import CompanyKnowledgeBase
from sqlalchemy import create_engine, inspect


def test_policy_edit_changes_version_without_changing_old_evidence(tmp_path):
    path = tmp_path / "policies.json"
    document = {
        "id": "delivery",
        "title": "Delivery",
        "category": "delivery",
        "text": "Investigate a missing parcel with the carrier.",
    }
    path.write_text(json.dumps([document]))
    knowledge = CompanyKnowledgeBase(path)
    original = knowledge.search("missing parcel")[0]
    document["text"] = "A specialist reviews every missing parcel."
    path.write_text(json.dumps([document]))
    changed = knowledge.search("missing parcel")[0]
    assert original.version != changed.version
    assert "carrier" in original.text
    assert "specialist" in changed.text
    assert knowledge.search("zzzzzzzz") == []


def test_legacy_migration_backs_up_data_and_is_repeatable(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY, customer_id INTEGER,
                customer_name TEXT, customer_email TEXT, feedback_text TEXT,
                sentiment TEXT, category TEXT, urgency TEXT, ai_response TEXT,
                created_at DATETIME
            );
            INSERT INTO feedback VALUES (
                1, 1, 'Alex', 'alex@example.com', 'Original message',
                'negative', 'product', 'high', 'Original draft',
                '2026-05-20 12:00:00'
            );
        """)
    engine = create_engine(f"sqlite:///{path}")
    init_db(engine)
    init_db(engine)
    backups = list(tmp_path.glob("legacy.db.backup-*"))
    assert len(backups) == 1
    with sqlite3.connect(path) as db:
        row = db.execute(
            "SELECT feedback_text, ai_response, status FROM feedback"
        ).fetchone()
        assert row == ("Original message", "Original draft", "open")
    with sqlite3.connect(backups[0]) as db:
        columns = [c[1] for c in db.execute("PRAGMA table_info(feedback)")]
        assert "status" not in columns
    assert "approvals" in inspect(engine).get_table_names()
