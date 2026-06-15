# CLAUDE.md

Quick reference for Claude (and Claude Code) working in this repo. The **canonical guide is [`AGENTS.md`](./AGENTS.md)** — read it first; this file only adds Claude-specific notes.

## Start here

1. Read [`AGENTS.md`](./AGENTS.md) (structure, the `Analyzer` contract, the disciplines).
2. Read [`spec.md`](./spec.md) for the technical detail of each analyzer and the data models.
3. Before editing, skim the relevant `analyzers/<name>/` module and its tests.

## The mental model in one line

A platform (`core/`) + five pluggable analyzers (`analyzers/`), each implementing `Analyzer` (`name` / `required_inputs` / `run -> RunResult` / `evaluate`) and emitting `Finding`s into one shared table.

## Do

- Keep each analyzer **isolated** behind the contract; emit `Finding`s, keep detail in the analyzer's own tables.
- Keep `run()` **idempotent** (delete-then-recompute).
- Use **`Decimal`** for money; the **config-driven Groq model** (`llama-3.1-8b-instant`, never `llama3-8b-8192`); **graceful degradation** if no key.
- Use the **right evaluation metric per analyzer type** (PR-AUC for AML — never accuracy; macro-F1 for categorization; match precision/recall for reconciliation; workflow metrics for disputes; grounding for reporting).
- After any change, verify a **clean clone builds and `pytest` is green**, and run `git status --ignored` (the `lib/`-in-`.gitignore` trap has bitten this repo).

## Don't

- Don't let the LLM **decide, resolve, or file** anything — it only explains/drafts/checks; generated artifacts are `pending_review`.
- Don't add microservices, Docker-into-the-core, or a second language — this is a modular monolith on purpose.
- Don't claim an analyzer is "done" because a shallow test passes. "Done" = substantive, runs end to end producing `Finding`s, honest `evaluate()` numbers, green from a clean clone.
- Don't introduce label/injection-revealing features in ML analyzers; split by account/time.

## Verify, don't assume

Walkthroughs in this project have outrun the code before (fabricated metrics, a 0%-lift ensemble, a regex-stub categorizer, missing committed files). When asked whether something works, **run it** — `pytest`, `evaluate`, and an end-to-end `run <analyzer>` — and report the real result.
