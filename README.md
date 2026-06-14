# Transaction-and-AML-Detection-System

A system that monitors card-payment transactions and flags suspicious ones — both **fraud** (a single transaction looks wrong) and **AML / money-laundering patterns** (a *sequence* looks like laundering). A Python backend does the detection (rules + classical ML for scoring, an LLM for plain-English explanations); a Next.js/React/TypeScript dashboard (later) visualizes the results.

Built phase by phase. See `transaction-aml-detection-implementation-plan.md` for the full v0→v11 roadmap.

**Current status: v0 — walking skeleton (ingest → store → summarize).**

## What v0 does

- A Typer CLI with two commands.
- `ingest <file.csv>` — validates each row against the internal schema (Pydantic), normalizes it, and stores it in SQLite. **Idempotent**: re-ingesting the same file inserts nothing. Invalid rows are skipped and counted, not fatal.
- `summary` — prints total count, total amount, date range, and a per-currency breakdown (rich-formatted).

No detection yet — v0 only proves the data path end to end.

## Run it (uv)

```bash
cd backend
uv sync
uv run python -m app.cli ingest sample.csv
uv run python -m app.cli summary
```

(Or with plain pip: `pip install -e .` then `python -m app.cli ...`.)

## Test

```bash
cd backend
uv run pytest -q
```

Covers ingest counts, idempotent re-ingest, and summary correctness against a temp database.

## Design notes (v0)

- **`Decimal` for money, never float** — this is a payments system; float rounding on money is a real bug.
- **`transaction_id` is the primary key** — duplicate rejection at the DB level is the backbone of idempotency.
- **stdlib `csv`, not pandas** — pandas earns its place at v5 (ML feature engineering); v0 doesn't need it.
- **Skip-and-count invalid rows** — ingest reports inserted / skipped-duplicate / skipped-invalid rather than aborting on one bad row.
- **Config-driven `DATABASE_URL`** — SQLite locally, swappable to Postgres at deploy, and a temp DB in tests.

## Layout

```
backend/
  app/
    cli.py              # Typer CLI (ingest, summary)
    config.py           # settings (DATABASE_URL)
    ingest/
      schema.py         # Pydantic TransactionBase (the internal shape)
      loader.py         # CSV -> validate -> idempotent insert
    storage/
      models.py         # SQLAlchemy ORM (Transaction)
      db.py             # engine + session + init_db
      queries.py        # read-side summary query
  tests/test_v0.py
  sample.csv
  pyproject.toml
```

## Roadmap

v0 ingest/store/summary · v1 synthetic data generator (labeled anomalies) · v2 rules · v3 risk scoring · v4 behavioral baselines · v5 classical ML · v6 LLM explanations · v7 API · v8 evaluation scorecard · v9–v11 Next.js dashboard + deploy
# Transactional-and-AML-Detection-System
