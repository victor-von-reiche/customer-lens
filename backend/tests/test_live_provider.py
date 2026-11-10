"""Gemini REST contracts exercised through in-memory HTTP responses."""

import asyncio
import json

import httpx
import pytest
from app.services.analysis_errors import describe_error
from app.services.classification import LiveProvider
from pydantic import ValidationError

LABELS = {
    "sentiment": "positive",
    "category": "service",
    "urgency": "low",
    "explanation": "General praise for the store.",
}


def completion(payload=None, finish_reason="STOP"):
    """Build a synthetic Gemini response without network access."""
    return {
        "candidates": [
            {
                "finishReason": finish_reason,
                "content": {
                    "parts": [{"text": json.dumps(payload or LABELS)}]
                },
            }
        ],
        "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 10},
    }


def test_live_client_requests_schema_and_validates_gemini_response():
    async def run():
        def handler(request):
            assert request.headers["x-goog-api-key"] == "test-only"
            assert request.url.host == "generativelanguage.googleapis.com"
            assert request.url.path.endswith(
                "gemini-3.5-flash-lite:generateContent"
            )
            assert not request.url.query
            body = json.loads(request.content)
            assert "temperature" not in body["generationConfig"]
            assert "thinkingConfig" not in body["generationConfig"]
            schema = body["generationConfig"]["responseJsonSchema"]
            assert schema["properties"]["sentiment"]["enum"] == [
                "positive",
                "negative",
                "neutral",
                "mixed",
            ]
            assert (
                body["generationConfig"]["responseMimeType"]
                == "application/json"
            )
            return httpx.Response(200, json=completion())

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            provider = LiveProvider(
                "test-only", "gemini-3.5-flash-lite", client
            )
            result, usage = await provider.classify("Best store ever!")
            assert result.sentiment == "positive"
            assert result.category == "service"
            assert usage.input_tokens == 20

    asyncio.run(run())


def test_blocked_or_truncated_output_is_not_a_classification():
    async def run():
        for body in [
            {"promptFeedback": {"blockReason": "SAFETY"}},
            completion(finish_reason="MAX_TOKENS"),
        ]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json=body)
                )
            ) as client:
                provider = LiveProvider(
                    "test-only", "gemini-2.5-flash", client
                )
                with pytest.raises(ValueError):
                    await provider.classify("Example")

    asyncio.run(run())


def test_authentication_diagnostics_do_not_leak_provider_payloads():
    async def run():
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(
                400,
                json={
                    "error": {
                        "message": "API key not valid: private-key-value",
                        "status": "INVALID_ARGUMENT",
                    }
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            provider = LiveProvider(
                "private-key-value", "gemini-2.5-flash", client
            )
            with pytest.raises(httpx.HTTPStatusError) as caught:
                await provider.classify("Best shop ever!")
            issue = describe_error(caught.value)
            assert issue.code == "authentication_failed"
            assert "backend/.env" in issue.message
            assert "private-key-value" not in issue.message
            assert len(calls) == 1

    asyncio.run(run())


def test_invalid_classification_label_is_rejected():
    async def run():
        invalid = {**LABELS, "sentiment": "great", "category": "unknown"}
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=completion(invalid))
            )
        ) as client:
            provider = LiveProvider("test-only", "gemini-2.5-flash", client)
            with pytest.raises(ValidationError):
                await provider.classify("Example")

    asyncio.run(run())


def test_context_is_sent_as_untrusted_data_in_original_language():
    async def run():
        history = [{"sender": "customer", "content": "Mein Paket fehlt."}]

        def handler(request):
            body = json.loads(request.content)
            data = json.loads(body["contents"][0]["parts"][0]["text"])
            assert data["customer_message"] == "Es ist noch nicht da."
            assert data["history"] == history
            assert len(body["contents"]) == 1
            assert body["systemInstruction"]["parts"][0]["text"]
            return httpx.Response(
                200,
                json=completion(
                    {
                        "sentiment": "negative",
                        "category": "delivery",
                        "urgency": "high",
                        "explanation": "Parcel still missing.",
                    }
                ),
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            provider = LiveProvider("test-only", "gemini-2.5-flash", client)
            result, _ = await provider.classify(
                "Es ist noch nicht da.",
                history=history,
            )
            assert result.category == "delivery"

    asyncio.run(run())


def test_transient_error_is_retried_once():
    async def run():
        calls = []

        def handler(request):
            calls.append(request)
            if len(calls) == 1:
                return httpx.Response(503, json={"error": {"message": "Busy"}})
            return httpx.Response(200, json=completion())

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            provider = LiveProvider("test-only", "gemini-2.5-flash", client)
            result, _ = await provider.classify("Best store ever!")
            assert result.category == "service"
            assert len(calls) == 2

    asyncio.run(run())


def test_quota_failure_is_not_retried_or_converted_to_neutral():
    async def run():
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(
                429,
                json={
                    "error": {
                        "message": "Daily quota exhausted",
                        "status": "RESOURCE_EXHAUSTED",
                    }
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            provider = LiveProvider("test-only", "gemini-2.5-flash", client)
            with pytest.raises(httpx.HTTPStatusError) as caught:
                await provider.classify("One of the best stores ever!")
            assert describe_error(caught.value).code == "quota_exceeded"
            assert len(calls) == 1

    asyncio.run(run())
