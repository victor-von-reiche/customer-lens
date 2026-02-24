from fastapi import FastAPI
from app.database.db import init_db
from app.api import feedback

# Create our FastAPI application
app = FastAPI(
    title="CustomerLens",
    description="AI-Powered Customer Feedback Intelligence Platform",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Run when the application starts"""
    init_db()
    print("Database initialized!")


# Include our feedback router
app.include_router(feedback.router)


# Welcome endpoint
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to CustomerLens!",
        "status": "API is running",
        "version": "1.0.0"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}