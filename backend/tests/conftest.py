"""Isolated database and deterministic provider fixtures."""

import os

os.environ["APP_MODE"] = "demo"
os.environ["DEMO_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_API_TOKEN"] = ""
os.environ["RAG_BACKEND"] = "lexical"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import get_db
from app.main import app, request_times
from app.models.feedback import Base


@pytest.fixture
def db():
    """Create a fresh SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    """Exercise real API routes without startup seeding or network calls."""
    app.dependency_overrides[get_db] = lambda: db
    request_times.clear()
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
    app.dependency_overrides.clear()
