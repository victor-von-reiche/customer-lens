"""Application settings and paths."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Read explicit runtime settings without requiring demo credentials."""

    mode: str = os.getenv("APP_MODE", "live")
    database_url: str = os.getenv(
        "DEMO_DATABASE_URL"
        if os.getenv("APP_MODE", "live") == "demo"
        else "DATABASE_URL",
        "",
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv(
        "GOOGLE_API_KEY", ""
    )
    model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    admin_token: str = os.getenv("ADMIN_API_TOKEN", "")
    rag_backend: str = os.getenv("RAG_BACKEND", "lexical")
    input_price: float | None = (
        float(os.environ["INPUT_PRICE_PER_MILLION"])
        if os.getenv("INPUT_PRICE_PER_MILLION")
        else None
    )
    output_price: float | None = (
        float(os.environ["OUTPUT_PRICE_PER_MILLION"])
        if os.getenv("OUTPUT_PRICE_PER_MILLION")
        else None
    )

    def __post_init__(self):
        if self.mode not in {"demo", "live"}:
            raise ValueError("APP_MODE must be demo or live")
        if self.rag_backend not in {"lexical", "chroma"}:
            raise ValueError("RAG_BACKEND must be lexical or chroma")
        if not self.database_url:
            name = "demo.db" if self.mode == "demo" else "customer_lens.db"
            object.__setattr__(
                self, "database_url", f"sqlite:///{BACKEND_DIR / name}"
            )


settings = Settings()
