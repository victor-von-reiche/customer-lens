"""Database sessions and additive legacy migration."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.customer import Customer  # noqa: F401
from app.models.feedback import Base
from app.models.message import Message  # noqa: F401

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@event.listens_for(engine, "connect")
def enable_foreign_keys(connection, _):
    """Enforce SQLite foreign keys on every connection."""
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")


def init_db(db_engine=engine):
    """Back up and extend existing SQLite tickets without deleting data."""
    inspector = inspect(db_engine)
    if "feedback" in inspector.get_table_names():
        columns = {item["name"] for item in inspector.get_columns("feedback")}
        additions = {
            "status": "VARCHAR(30) NOT NULL DEFAULT 'open'",
            "analysis_status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
            "updated_at": "DATETIME",
            "resolved_at": "DATETIME",
        }
        missing = additions.keys() - columns
        if missing:
            if db_engine.dialect.name != "sqlite":
                raise RuntimeError("Legacy migration supports SQLite only")
            database = db_engine.url.database
            if database and database != ":memory:":
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
                backup = Path(f"{database}.backup-{stamp}")
                with sqlite3.connect(database) as source:
                    with sqlite3.connect(backup) as target:
                        source.backup(target)
            with db_engine.begin() as connection:
                for name in sorted(missing):
                    definition = additions[name]
                    connection.execute(
                        text(
                            f"ALTER TABLE feedback ADD COLUMN {name} "
                            f"{definition}"
                        )
                    )
                connection.execute(
                    text(
                        "UPDATE feedback SET updated_at = created_at "
                        "WHERE updated_at IS NULL"
                    )
                )
    Base.metadata.create_all(db_engine)
    with db_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_approval_analysis "
                "ON approvals (analysis_id)"
            )
        )


def get_db():
    """Provide a request-scoped session and roll back failures."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
