"""
Database connection and session management
This file handles connecting to our SQLite database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.feedback import Base

# Database URL - SQLite file will be created in project root
DATABASE_URL = "sqlite:///./customer_lens.db"

# Create database engine
# Think of this as opening the connection to our database file
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
# Sessions are like "conversations" with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database.
    Creates all tables if they don't exist yet.

    Think of this like: "Set up the filing cabinet with all its drawers"
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get database session.

    This is a dependency that FastAPI will use to give us
    a database connection for each request.

    Think of it like: "Open the filing cabinet, do some work, then close it"
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()