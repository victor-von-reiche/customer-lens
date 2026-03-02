"""
CustomerLens - AI-Powered Customer Feedback Intelligence Platform
Main FastAPI application entry point
"""

from fastapi import FastAPI
from app.database.db import init_db
from app.api import feedback
from app.rag.vectorstore import knowledge_base
from app.models.customer import Customer

app = FastAPI(
    title="CustomerLens",
    description="AI-Powered Customer Feedback Intelligence Platform for AURON",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and load guidelines into vector store."""
    init_db()
    print("Database initialized")

    knowledge_base.load_guidelines("company_guidelines.txt")
    print("Knowledge base ready")


app.include_router(feedback.router)


@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to CustomerLens - AURON Customer Feedback System",
        "status": "API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}