"""Evaluate classification, retrieval, latency, and response boundaries."""

import argparse
import asyncio
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter

from app.config import settings
from app.rag.vectorstore import CompanyKnowledgeBase
from app.services.classification import DemoProvider, LiveProvider

ROOT = Path(__file__).resolve().parents[1]


async def evaluate(mode, limit=None, knowledge=None):
    """Run labeled synthetic cases without using the application's database."""
    if mode == "live" and not settings.gemini_api_key:
        raise ValueError(
            "Live evaluation requires GEMINI_API_KEY or GOOGLE_API_KEY"
        )
    provider = (
        DemoProvider()
        if mode == "demo"
        else LiveProvider(settings.gemini_api_key, settings.model)
    )
    knowledge = knowledge or CompanyKnowledgeBase(backend=settings.rag_backend)
    cases = json.loads((ROOT / "evaluation/cases.json").read_text())
    rows = []
    for case in cases[:limit]:
        started = perf_counter()
        row = {
            "id": case["id"],
            "tag": case["tag"],
            "expected": case["expected"],
            "ok": False,
            "input_tokens": 0,
            "output_tokens": 0,
        }
        try:
            result, usage = await provider.classify(case["text"])
            row["input_tokens"] += usage.input_tokens
            row["output_tokens"] += usage.output_tokens
            query = f"{result.category} {case['text']}"
            if result.urgency == "critical":
                query += " safety injury brake failure"
            elif result.sentiment == "positive":
                query += " positive feedback"
            sources = await asyncio.to_thread(knowledge.search, query)
            draft, usage = await provider.draft(
                case["text"], result, sources, []
            )
            row["input_tokens"] += usage.input_tokens
            row["output_tokens"] += usage.output_tokens
            row.update(
                {
                    "predicted": result.model_dump(),
                    "sources": [source.id for source in sources],
                    "source_hit": case["expected_source"]
                    in {source.id for source in sources},
                    "response": draft.response,
                    "citation_valid": set(draft.cited_source_ids)
                    <= {source.id for source in sources},
                    "boundary_pass": draft.needs_review
                    and not any(
                        word in draft.response
                        for word in case.get("forbidden_output", [])
                    ),
                    "ok": True,
                }
            )
        except Exception as error:
            row["error"] = type(error).__name__
        row["latency_ms"] = round((perf_counter() - started) * 1000)
        rows.append(row)
    if isinstance(provider, LiveProvider):
        await provider.client.aclose()
    successful = [row for row in rows if row["ok"]]
    critical = [r for r in rows if r["expected"]["urgency"] == "critical"]
    accuracy = {
        key: sum(
            row["ok"] and row["predicted"][key] == row["expected"][key]
            for row in rows
        )
        / len(rows)
        for key in ("sentiment", "category", "urgency")
    }
    latencies = sorted(row["latency_ms"] for row in rows)
    cost = None
    if mode == "demo":
        cost = 0
    elif (
        settings.input_price is not None and settings.output_price is not None
    ):
        cost = (
            sum(
                row["input_tokens"] * settings.input_price
                + row["output_tokens"] * settings.output_price
                for row in rows
            )
            / 1_000_000
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "model": provider.model,
        "retrieval": settings.rag_backend,
        "policy_version": knowledge.version,
        "dataset": "52 authored synthetic cases, including 4 injection probes",
        "limitations": (
            "Demo scores describe keyword rules, not AI quality. This small "
            "synthetic set is not a held-out production benchmark. Boundary "
            "checks do not establish factual correctness or injection safety."
        ),
        "summary": {
            "cases": len(rows),
            "failures": len(rows) - len(successful),
            "accuracy": accuracy,
            "critical_recall": sum(
                row["ok"] and row["predicted"]["urgency"] == "critical"
                for row in critical
            )
            / len(critical)
            if critical
            else None,
            "retrieval_hit_rate_at_3": sum(
                row.get("source_hit", False) for row in rows
            )
            / len(rows),
            "boundary_pass_rate": sum(
                row.get("boundary_pass", False) for row in rows
            )
            / len(rows),
            "citation_valid_rate": sum(
                row.get("citation_valid", False) for row in rows
            )
            / len(rows),
            "latency_mean_ms": round(mean(latencies)),
            "latency_p95_ms": latencies[math.ceil(len(rows) * 0.95) - 1],
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "output_tokens": sum(r["output_tokens"] for r in rows),
            "estimated_cost_usd": cost,
        },
        "results": rows,
    }


def main():
    """Write a report and require explicit opt-in for live calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "evaluation/demo-report.json"
    )
    args = parser.parse_args()
    if args.mode == "live" and not args.allow_live:
        parser.error(
            "Live evaluation is billable; pass --allow-live explicitly"
        )
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    report = asyncio.run(evaluate(args.mode, args.limit))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
