"""CustomerLens application and safe demo startup."""

import asyncio
import hmac
import logging
import os
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.feedback import router
from app.config import settings
from app.database.db import SessionLocal, init_db
from app.models.feedback import Analysis, Feedback
from app.services.demo import seed_demo
from app.services.rag_response import knowledge_base

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app):
    """Initialize storage, recover interrupted attempts, and seed demo data."""
    if settings.mode == "live" and not settings.gemini_api_key:
        raise ValueError(
            "Live mode requires GEMINI_API_KEY or GOOGLE_API_KEY; use --demo"
        )
    init_db()
    await asyncio.to_thread(knowledge_base.load_guidelines)
    with SessionLocal() as db:
        db.query(Analysis).filter_by(status="processing").update(
            {
                "status": "failed",
                "error": "Server restarted; retry analysis.",
            }
        )
        db.query(Feedback).filter_by(analysis_status="processing").update(
            {
                "analysis_status": "failed",
                "ai_response": None,
                "sentiment": None,
                "category": None,
                "urgency": None,
            }
        )
        db.commit()
        if settings.mode == "demo":
            await seed_demo(db)
    yield


app = FastAPI(
    title="CustomerLens",
    root_path=os.getenv("ROOT_PATH", ""),
    version="2.0.0",
    lifespan=lifespan,
    description="Support triage for fictional bike brand AURON.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
request_times = defaultdict(deque)


@app.middleware("http")
async def protect_api(request: Request, call_next):
    """Apply optional bearer access and bound costly mutation requests."""
    if request.url.path.startswith("/feedback"):
        if settings.admin_token and request.method != "OPTIONS":
            expected = f"Bearer {settings.admin_token}"
            if not hmac.compare_digest(
                request.headers.get("authorization", ""), expected
            ):
                return JSONResponse({"detail": "Access token required"}, 401)
        if request.method == "POST":
            now = monotonic()
            key = request.client.host if request.client else "unknown"
            for old_key in list(request_times):
                if (
                    not request_times[old_key]
                    or now - request_times[old_key][-1] > 60
                ):
                    del request_times[old_key]
            times = request_times[key]
            while times and now - times[0] > 60:
                times.popleft()
            if len(times) >= 20:
                return JSONResponse(
                    {"detail": "Too many requests; retry in one minute"},
                    429,
                    headers={"Retry-After": "60"},
                )
            times.append(now)
    return await call_next(request)


app.include_router(router)


@app.get("/")
def root():
    """Describe the running API."""
    return {"name": "CustomerLens", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
def health_check():
    """Check database readiness without calling an AI provider."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "healthy", "mode": settings.mode}


@app.get("/config")
def public_config():
    """Expose non-secret runtime details for the interface."""
    return {
        "mode": settings.mode,
        "model": settings.model
        if settings.mode == "live"
        else "demo-rules-v1",
        "requires_token": bool(settings.admin_token),
        "retrieval": settings.rag_backend,
        "policy_version": knowledge_base.version,
    }
