# Evaluation

The dataset contains 52 authored synthetic English messages: 12 each for product,
delivery, pricing, and service, plus 4 prompt-injection probes. Each case has
expected sentiment, urgency, category, and a relevant source ID. Labels are
reviewable in `cases.json`; they are not independent production ground truth.

From the backend directory after installing its dependencies:

```bash
.venv/bin/python -m app.evaluate --output ../evaluation/demo-report.json
```

The generated demo report describes deterministic keyword rules and retrieval,
not Gemini quality. No paid API is called. Cases are not used as a runtime lookup
or to build the policy index. This small authored set is not a held-out benchmark.

For a billable live run, configure `backend/.env`, then explicitly opt in:

```bash
.venv/bin/python -m app.evaluate --mode live --allow-live --limit 5 --output ../evaluation/live-report.json
```

Remove `--limit` to run all cases (up to 104 provider requests before SDK retries).
The runner does not modify tickets. Inspect the JSON report for expected versus
predicted labels, retrieved IDs, draft text, latency, token usage, and failures.
Rates use all requested cases as denominator so provider errors cannot inflate
accuracy. Critical recall is measured among critical labeled cases. Retrieval
hit rate at 3 checks for the expected source among the three retrieved policies.

Cost estimates use explicitly configured per-million input and output rates and
exclude unreported failed requests and retries; they are not billing totals.
Without configured rates, live cost is null. Demo token usage and cost are zero.
Boundary checks only test review flags and a few forbidden output markers.
They do not establish factual accuracy, complete citation support, or injection
resistance. Manually review drafts, especially refunds, injuries, and ambiguous
messages. A future stronger benchmark should use independently labeled, held-out
messages with separate development and evaluation sets.

## Sentiment and category regression suite

`classification-cases.json` contains 86 synthetic cases, including the original
52 plus 34 regression cases for general store praise, German, negation, sarcasm,
mixed subjects, refund causes, prompt injection, and conversation references.
The expected labels were authored before the live evaluation. They are reviewable
judgments, not independent production ground truth.

```bash
.venv/bin/python -m app.evaluate_classification --mode live --allow-live --suite regression --requests-per-minute 6
```

This runner calls only Gemini classification, not response generation, and never
changes ticket data. It saves every input, expected/actual label, provider error,
token count, and disagreement. Errors count against accuracy. A live report
measures the configured Gemini model; the demo remains a limited rule simulation.

Live evaluation is paced at six requests per minute by default to leave room
for the application on a small Gemini quota. Use `--suite regression` to run
the 34 targeted cases; `--suite all` runs all 86. Quota errors are recorded as
provider failures and never counted as valid classifications.
