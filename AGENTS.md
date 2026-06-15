# AGENTS.md

Guidance for AI agents and human contributors working in this repository. Read this before making changes.

## What this project is

A **transaction-analysis platform** with a shared backbone (`core/`) and five pluggable **analyzers** (`analyzers/`): `aml`, `reconciliation`, `categorization`, `disputes`, `reporting`. Each analyzer is an isolated module implementing one contract and emitting `Finding`s into a shared table. This is a **modular monolith**, not microservices — keep it that way.

## Repository layout

```
core/
  analyzer.py     # the Analyzer contract (Protocol) every analyzer implements
  registry.py     # analyzer registration + lookup
  pipeline.py     # runs an analyzer end to end
  llm.py          # the single Groq client (shared by all LLM-using analyzers)
  config.py       # settings (DATABASE_URL, GROQ_*, per-analyzer config)
  store/          # SQLAlchemy: base, db session, models (Transaction, Finding, AuditLog), queries
  ingest/         # multi-source ingestion (loader, adapters)
analyzers/<name>/
  analyzer.py     # implements Analyzer; registers itself
  models.py       # the analyzer's own domain tables
  <domain>.py     # the analyzer's logic
data/             # seeded synthetic generators + Kaggle adapter
interface/        # cli.py (Typer), api.py (FastAPI)
frontend/         # Next.js dashboard
tests/<name>/     # per-analyzer tests
```

## The Analyzer contract

Every analyzer implements this (see `core/analyzer.py`):

```python
class Analyzer(Protocol):
    name: str
    def required_inputs(self) -> list[str]        # e.g. ["transactions"], ["ledger","processor"]
    def run(self, session, config) -> RunResult     # process inputs, persist Findings (idempotent)
    def evaluate(self, session) -> Optional[str]     # markdown scorecard section, or None
```

### How to add a new analyzer

1. Create `analyzers/<name>/` with `analyzer.py`, `models.py`, and your logic files.
2. Implement the `Analyzer` contract in `analyzer.py`; emit `Finding`s, keep domain detail in your own tables.
3. **Register it** (the analyzer module must be imported so registration runs — see how the existing analyzers are imported in `interface/cli.py`).
4. Add a synthetic data generator in `data/` if the analyzer needs its own input shape, with **injected ground-truth** so it can be evaluated.
5. Implement `evaluate()` with the **correct metric for the analyzer type** (see below).
6. Add tests under `tests/<name>/`.
7. Surface it in the CLI (`run <name>`) and, if needed, the API and dashboard.

## Non-negotiable disciplines

These are enforced across the codebase. Match them:

- **Idempotent runs.** A `run()` must be safely re-runnable: delete the analyzer's prior `Finding`s/results, then recompute. No duplicates, no stale rows.
- **`Decimal` for money.** Never floats for currency amounts (convert to float only inside ML feature matrices).
- **Config-driven LLM model.** The Groq model id lives in `core/config.py` (`llama-3.1-8b-instant` or current). **Never hardcode a model**, and never use `llama3-8b-8192` (decommissioned).
- **Graceful LLM degradation.** If `GROQ_API_KEY` is missing or the API errors, the analyzer must still complete (skip the LLM step, warn) — the pipeline never depends on a third-party LLM being up.
- **LLM explains/drafts/checks, never decides.** No LLM creates or removes a detection, resolves a break, or files a report. Generated artifacts are `status="pending_review"`.
- **No leakage (ML analyzers).** Never use the label or an injection-revealing feature; split by account/time, not random row. State residual caveats.
- **Seeded generators / `random_state`.** Synthetic data and models are reproducible.
- **Clean-clone check after every change.** Run `git status --ignored` and confirm everything the code imports is committed and the repo builds + tests from a fresh clone. (A prior bug: `.gitignore`'s `lib/` rule silently excluded `frontend/src/lib/`. Watch for this class of error.)

## The evaluation rule (important)

Use the right metric for the analyzer type — mixing them is a red flag:

- **Imbalanced detection (AML):** precision / recall / F1 / **PR-AUC**. **Never accuracy** (~5% positives → "predict none" scores ~95%).
- **Balanced classification (categorization):** accuracy is acceptable, plus macro-F1 + confusion matrix.
- **Matching (reconciliation):** precision / recall on injected breaks, match-rate.
- **Workflow (disputes):** state-transition correctness, deadline handling, win rate — *not* classification metrics.
- **Generation (reporting):** grounding / faithfulness / completeness — **never precision/recall on generated text.**

## Commands

```bash
uv sync                                              # install
uv run python -m interface.cli generate ... --out d.csv
uv run python -m interface.cli ingest d.csv
uv run python -m interface.cli run <analyzer>        # aml | reconciliation | categorization | disputes | reporting
uv run python -m interface.cli train --labels d.csv  # AML ensemble (pass labels to enable the supervised booster)
uv run python -m interface.cli evaluate              # regenerate the combined SCORECARD.md
uv run python -m interface.cli findings --band critical
uv run pytest -q                                     # full suite (must be green)
```

## Conventions

- Findings are the shared surface; domain tables hold detail.
- Keep analyzers isolated — one analyzer must never import another's internals (the `reporting` analyzer reads shared `Finding`s, not other analyzers' code).
- Keep the README scorecard table and `SCORECARD.md` in sync (both come from `evaluate`).
- Don't commit logs, databases, model artifacts, or generated CSVs (gitignore them).

## The one rule about claims

Keep the claim matching the code. An analyzer is "done" when it is substantive (not a stub), runs end to end producing `Finding`s, passes tests from a clean clone, and reports honest numbers via `evaluate()`. Passing a shallow unit test is not "done."
