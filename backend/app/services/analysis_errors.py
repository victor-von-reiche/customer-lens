"""Public analysis diagnostics without credentials or raw provider payloads."""

from dataclasses import dataclass

import httpx
from pydantic import ValidationError


@dataclass(frozen=True)
class AnalysisIssue:
    code: str
    message: str


def describe_error(error):
    """Translate Gemini failures into actionable, sanitized diagnostics."""
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status in {400, 401, 403}:
            try:
                body = error.response.json().get("error", {})
            except ValueError:
                body = {}
            reason = str(body).lower()
            if (
                status in {401, 403}
                or "api_key" in reason
                or "api key" in reason
            ):
                return AnalysisIssue(
                    "authentication_failed",
                    "Gemini rejected the credentials "
                    "or project access. Check GEMINI_API_KEY / GOOGLE_API_KEY "
                    "in backend/.env and restart the backend.",
                )
            return AnalysisIssue(
                "invalid_request",
                "Gemini rejected the request. Check the "
                "configured model and structured-output support.",
            )
        if status == 429:
            return AnalysisIssue(
                "quota_exceeded",
                "Gemini quota or rate limit reached. Check "
                "the project's quota/billing or retry later.",
            )
        if status == 404:
            return AnalysisIssue(
                "model_unavailable",
                "The configured Gemini model is not "
                "available. Check GEMINI_MODEL.",
            )
        return AnalysisIssue(
            "provider_unavailable", "Gemini is temporarily unavailable. Retry."
        )
    if isinstance(error, httpx.TimeoutException):
        return AnalysisIssue(
            "timeout", "Gemini timed out. Retry the analysis."
        )
    if isinstance(error, httpx.NetworkError):
        return AnalysisIssue(
            "connection_failed", "Cannot reach Gemini. Check the connection."
        )
    if isinstance(error, ValidationError | ValueError):
        return AnalysisIssue(
            "invalid_output",
            "Gemini returned an incomplete or invalid "
            "result. Retry or review this ticket manually.",
        )
    return AnalysisIssue(
        "analysis_unavailable",
        "Analysis unavailable. Review manually or retry.",
    )
