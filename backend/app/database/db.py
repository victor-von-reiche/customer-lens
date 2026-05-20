from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.feedback import Base

# Database URL - SQLite file will be created in project root
DATABASE_URL = "sqlite:///./customer_lens.db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()