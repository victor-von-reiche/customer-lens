"""Evaluate sentiment and category independently of reply generation."""

import argparse
import asyncio
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from app.config import settings
from app.services.analysis_errors import describe_error
from app.services.classification import (
    PROMPT_VERSION,
    DemoProvider,
    LiveProvider,
)

ROOT = Path(__file__).resolve().parents[2]


async def evaluate(
    mode,
    limit=None,
    concurrency=2,
    requests_per_minute=6,
    suite="all",
):
    """Compare real or simulated labels against authored regression cases."""
    if mode == "live" and not settings.gemini_api_key:
        raise ValueError(
            "Live evaluation requires GEMINI_API_KEY or GOOGLE_API_KEY"
        )
    provider = (
        DemoProvider()
        if mode == "demo"
        else LiveProvider(settings.gemini_api_key, settings.model)
    )
    cases = json.loads(
        (ROOT / "evaluation/classification-cases.json").read_text()
    )
    if suite == "regression":
        cases = [c for c in cases if not c["id"].startswith("case-")]
    cases = cases[:limit]
    pacing_lock = asyncio.Lock()
    next_request = 0.0
    semaphore = asyncio.Semaphore(concurrency)

    async def evaluate_case(case):
        row = {
            "id": case["id"],
            "text": case["text"],
            "tag": case["tag"],
            "expected": case["expected"],
            "ok": False,
        }
        async with semaphore:
            if mode == "live" and requests_per_minute:
                async with pacing_lock:
                    nonlocal next_request
                    await asyncio.sleep(max(0, next_request - monotonic()))
                    next_request = monotonic() + 60 / requests_per_minute
            try:
                result, usage = await provider.classify(
                    case["text"], history=case.get("history", [])
                )
                row.update(
                    {
                        "ok": True,
                        "predicted": result.model_dump(),
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                    }
                )
            except Exception as error:
                row["error"] = describe_error(error).code
        return row

    try:
        rows = await asyncio.gather(*(evaluate_case(case) for case in cases))
    finally:
        if isinstance(provider, LiveProvider):
            await provider.client.aclose()
    successful = [row for row in rows if row["ok"]]
    fields = ("sentiment", "category", "urgency")
    correct = {
        field: sum(
            row["ok"] and row["predicted"][field] == row["expected"][field]
            for row in rows
        )
        for field in fields
    }
    mismatches = [
        row
        for row in rows
        if not row["ok"]
        or any(
            row["predicted"][field] != row["expected"][field]
            for field in fields
        )
    ]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "suite": suite,
        "model": provider.model,
        "prompt_version": PROMPT_VERSION,
        "limitations": (
            "Authored synthetic English/German cases, not a held-out "
            "production benchmark. Demo scores measure rules, not AI quality. "
            "Perfect accuracy is not guaranteed. No customer data is used."
        ),
        "summary": {
            "cases": len(rows),
            "failures": sum(not r["ok"] for r in rows),
            "correct": correct,
            "valid_responses": len(successful),
            "response_coverage": len(successful) / len(rows),
            "provider_errors": dict(
                Counter(
                    row.get("error", "unknown")
                    for row in rows
                    if not row["ok"]
                )
            ),
            "valid_response_accuracy": {
                field: count / len(successful) if successful else None
                for field, count in correct.items()
            },
            "accuracy": {
                field: count / len(rows) for field, count in correct.items()
            },
            "mismatched_cases": len(mismatches),
            "input_tokens": sum(r.get("input_tokens", 0) for r in rows),
            "output_tokens": sum(r.get("output_tokens", 0) for r in rows),
        },
        "mismatches": mismatches,
        "results": rows,
    }


def main():
    """Write regression results; require explicit opt-in for live calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--requests-per-minute", type=int, default=6)
    parser.add_argument(
        "--suite", choices=["all", "regression"], default="all"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "live" and not args.allow_live:
        parser.error("Live calls are billable; add --allow-live")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if not 1 <= args.concurrency <= 8:
        parser.error("--concurrency must be between 1 and 8")
    if not 1 <= args.requests_per_minute <= 60:
        parser.error("--requests-per-minute must be between 1 and 60")
    report = asyncio.run(
        evaluate(
            args.mode,
            args.limit,
            args.concurrency,
            args.requests_per_minute,
            args.suite,
        )
    )
    path = (
        args.output
        or ROOT / f"evaluation/classification-{args.mode}-report.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
