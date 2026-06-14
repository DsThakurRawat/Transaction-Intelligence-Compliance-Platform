# Transaction-and-AML-Detection-System — Implementation Plan

A system that monitors card-payment transactions and flags the suspicious ones — both **fraud** (this single transaction looks wrong) and **AML / money-laundering patterns** (this *sequence* of transactions looks like laundering). A **Python/FastAPI backend** does the real work — rule-based checks and classical ML produce a risk score per transaction, and an LLM writes a plain-English explanation of *why* each flag fired. A **Next.js / React / TypeScript dashboard** (Vercel-deployable, custom-designed) sits on top to show flagged transactions, risk scores, trends, and the explanations.

**Backend stack:** Python · FastAPI + uvicorn · pandas / numpy (data) · scikit-learn (anomaly detection) · scipy (statistics) · SQLite → Postgres (storage) · Groq (LLM explanations, OpenAI-compatible) · Typer (CLI) · rich (CLI output) · pytest.

**Frontend stack:** Next.js (App Router) · React · TypeScript · Tailwind CSS · a charting lib (Recharts) · deployed on Vercel.

**The detection philosophy (grounded in research):** rules are the honest baseline, classical ML is the upgrade that *cuts false positives* (well-tuned ML reduces false-positive rates ~60–80% versus rule-only baselines), and the **LLM never detects — it only explains.** Regulators demand to know *why* an alert fired; the explanation layer is the differentiator over plain rule engines, and it's where the "AI" genuinely earns its place.

---

## 0. How to read this

The plan is **versioned, not monolithic**, and built in two stages: **the backend first (v0–v8), the dashboard second (v9–v11).** This ordering is deliberate — the backend is the substance and your strength, so it gets built and proven (testable via CLI/API) before any frontend exists. The dashboard is then a view layer on a working system. If you stop at v8, you still have a complete, demoable backend.

**Each version is runnable, and each ends with a test you run before moving on** — that's the "implement and test one by one" contract. Every version states: the goal, what it adds, what now works, the gaps it knowingly keeps, how to test it, and the key decisions (with the rejected alternative).

Two disciplines carry through. First: **the logic is yours, the heavy ML is borrowed** — you build the rules, scoring, profiling, pipeline, API, and dashboard; you call libraries for the ML model, the statistics, and the LLM. Second: **every detection feature ships with the number that proves it** — precision, recall, false-positive rate, detection-rate-by-pattern. A fraud detector with no measured accuracy is a demo; one with a precision/recall scorecard is a portfolio piece. That scorecard is possible because the synthetic data carries **known, labeled anomalies** (Section 4).

---

## 1. Architecture — the layers

- **Ingestion + normalization** — read transactions (CSV first, then JSON/API), validate, and normalize into one internal schema (consistent fields, types, timestamps, currency).
- **Storage** — SQLite locally (zero infra), Postgres when deployed. Holds transactions, scan runs, flags/scores, and an append-only audit log.
- **Detection pipeline (the spine)** — the ordered path every transaction goes through: rules → score → behavioral profile → ML → explanation. Everything else is a component this pipeline calls.
- **Rule engine** — explainable, deterministic checks (amount thresholds, velocity, structuring, geo/time anomalies, high-risk merchant categories). The baseline.
- **Risk scorer** — combines signals (rule hits + behavioral deviation + ML score) into a single 0–100 risk score with severity bands, and ranks flagged items.
- **Behavioral profiler** — per-account baselines (normal amount, frequency, geography) so the system can flag "this breaks *this account's* normal pattern," not just global rules.
- **ML detector** — classical anomaly detection (Isolation Forest) on engineered features; optionally a supervised classifier (we have labels from the generator). This is AI core #1.
- **LLM explainer** — for each flagged item, turns the signals into a concise plain-English reason + suggested analyst action. This is AI core #2 (explanation, not detection).
- **API layer** — FastAPI exposing the data the dashboard needs (flagged transactions, scores, explanations, run summaries), OpenAPI-documented.
- **Frontend** — Next.js/React/TS dashboard consuming the API.
- **Data generator** — produces synthetic card transactions with **injected, labeled anomalies** — the ground truth for the accuracy numbers and the demo data.
- **Eval harness** — runs the full pipeline against the labeled data and computes the scorecard.

## 2. The scan path (the spine)

Every transaction flows through one path; each version below adds a station:

```
transaction
  → [v0] ingest + normalize + store
  → [v2] rule engine        (which rules fired, why)
  → [v4] behavioral profile (deviation from this account's baseline)
  → [v5] ML detector        (anomaly score from features)
  → [v3] risk scorer        (combine signals → 0–100 score + severity)
        flagged?  → yes ↓        no → record clean, done
  → [v6] LLM explainer       (plain-English reason + suggested action)
  → [v7] expose via API      (→ [v9] dashboard renders it)
  → log the run + audit trail
```

## 3. Build-vs-borrow stance

**Build (this is the project and the résumé signal):** ingestion/normalization, the transaction schema, the rule engine, the risk scorer, the behavioral profiler, the detection pipeline, the FastAPI layer, the Next.js dashboard, the synthetic data generator, and the eval harness.

**Borrow:** the ML model (scikit-learn Isolation Forest / classifier), the statistics (scipy/numpy), data handling (pandas), the LLM (Groq via its OpenAI-compatible API — model kept in config, never hardcoded, because providers churn model IDs), CLI niceties (Typer, rich), and charts (Recharts).

**Decision — detection is rules + classical ML, not an LLM.** LLMs don't reliably detect numeric/behavioral anomalies and are expensive per call; statistics/ML is the right tool. *Rejected:* "ask the LLM if each transaction is fraud." **The LLM's job is explanation**, where it's genuinely strong and where it's the differentiator.

---

## 4. The data strategy (where the data comes from)

You don't need real production data — and shouldn't use it. The primary source is **synthetic data you generate, with deliberately injected, labeled anomalies.** This is a feature, not a shortcut:

- **You control the ground truth** — you know exactly which transactions are fraud/laundering and which pattern each represents, so you can *measure* detection (precision, recall, F1, detection-rate-by-pattern). That's the scorecard.
- **No privacy or access problems**, runs anywhere, costs nothing.
- **It demos cleanly** — "watch: I inject a structuring pattern, run a scan, and the system flags it and explains why."

The generator (v1) produces realistic card transactions — account, timestamp, amount, currency, merchant, merchant-category (MCC), country, channel — for a population of accounts with normal behavior, then injects labeled anomaly patterns:
- **Fraud patterns:** an unusually large charge; a burst of rapid transactions (velocity); a charge from an unexpected country; activity on a long-dormant account.
- **AML patterns:** **structuring/smurfing** (many transactions just under a reporting threshold); rapid in-and-out movement; fan-in/fan-out across many counterparties.

Optionally, later, run the system against a **public dataset** (e.g. a Kaggle credit-card-transactions set) or replay it over time for added realism — but synthetic-with-labels is what gives you the numbers.

---

## 5. The versioned build

### Stage 1 — The backend (v0–v8)

### v0 — Walking skeleton: ingest → store → summarize
- **Goal.** Prove the data path end to end with the least machinery.
- **Adds.** A Typer CLI; `ingest <file.csv>` that validates and normalizes transactions into the internal schema and stores them in SQLite; `summary` that prints count, total amount, date range, and a breakdown by status/currency (using rich).
- **Works.** You can load a CSV of transactions and see an accurate summary.
- **Retained gaps.** No detection of any kind yet; tiny hand-made sample CSV only.
- **Test.** Ingest a small known CSV; the summary numbers match a hand count. Re-ingesting is idempotent (no duplicate rows).
- **Decisions.** SQLite first (versus Postgres) — zero infra, file-based, perfect for local build; swap to Postgres at deploy (v11). One normalized internal schema from day one so every later stage reads the same shape.

### v1 — Synthetic data generator (the ground truth)
- **Goal.** Produce realistic transactions with **known, labeled anomalies**.
- **Adds.** `generate --accounts N --days D --out data.csv` — simulates a population of accounts with normal spending behavior, then injects labeled anomaly patterns (fraud + AML, per Section 4). Emits a label column / sidecar (`is_anomaly`, `anomaly_type`).
- **Works.** One command produces a realistic dataset where you know the right answer for every row.
- **Retained gaps.** Patterns are hand-designed (fine — you want known patterns); not real-world-messy yet.
- **Test.** Generated data ingests cleanly into v0; the injected-anomaly fraction matches what you asked for; normal vs. anomalous rows are distinguishable by construction.
- **Decisions.** Labeled synthetic data as the foundation (versus scraping real data) — it's the only way to *measure* detection accuracy, and it doubles as demo data and is privacy-clean.

### v2 — Rule-based detection (the baseline)
- **Goal.** Catch the obvious cases with explainable, deterministic rules.
- **Adds.** A small rule engine; each rule is a named, documented check that emits a flag with a human reason. Starter rules: amount over threshold; velocity (≥N transactions in M minutes); **structuring** (multiple transactions just under a round/reporting limit); odd-hour activity; high-risk merchant category; country mismatch. `scan` runs the rules and stores flags (which rule, why).
- **Works.** A scan flags transactions that trip rules, each with a plain reason; on the synthetic data it catches the blunt anomalies.
- **Retained gaps.** Rules are rigid (fixed thresholds → false positives); no scoring/ranking; no per-account context.
- **Test.** On generated data, confirm the rules catch the obvious injected anomalies; inspect a few flags and confirm the reason is correct. Note the false-positive count — the number ML will improve.
- **Decisions.** Rules first (versus jumping to ML) — they're the honest baseline you measure ML against, they're fully explainable, and they encode real fraud/AML typologies (e.g. structuring) directly.

### v3 — Risk scoring + ranking
- **Goal.** Turn binary rule hits into a prioritized risk score.
- **Adds.** A scorer that combines signals into a single **0–100 risk score** per transaction (config-driven weights per rule), with severity bands (low/medium/high/critical), plus an aggregate score per account. `scan` now ranks flagged items by score.
- **Works.** Output is a ranked list — the riskiest transactions first — instead of an unordered pile of flags.
- **Retained gaps.** Weights are hand-set; only rule signals feed the score so far (behavioral + ML join in v4/v5).
- **Test.** Confirm higher-risk injected anomalies score above borderline ones; confirm severity bands are sensible; changing a weight in config changes ranking as expected.
- **Decisions.** A single normalized score with config-driven weights (versus per-rule alerts) — analysts triage by priority, and the score is the column the dashboard sorts on.

### v4 — Behavioral profiling (statistical)
- **Goal.** Flag what's abnormal *for this account*, not just globally.
- **Adds.** Per-account baselines computed from history (mean/std amount, typical frequency, usual countries/merchant-categories); deviation checks (z-score on amount, velocity-vs-baseline, first-time-country, first-time-category). These deviations feed the v3 score.
- **Works.** The system catches "this account normally spends ₹2k and just spent ₹90k" — context-aware anomalies a global rule misses.
- **Retained gaps.** Statistical, single-feature thresholds; multivariate patterns wait for ML.
- **Test.** Construct an account with a clear baseline then an out-of-pattern transaction; confirm it's flagged for deviation while the same amount on a high-spending account is not.
- **Decisions.** Per-account baselines (versus global thresholds only) — this is the bridge from rules to ML and reflects how real monitoring compares a customer to their own 90-day behavior.

### v5 — Classical ML detection (AI core #1)
- **Goal.** Catch multivariate anomalies rules and single-feature stats miss, and cut false positives.
- **Adds.** Feature engineering (amount, log-amount, hour/day, velocity features, merchant-category risk, geo features, account age, amount-vs-account-baseline, peer comparison); an **Isolation Forest** for an unsupervised anomaly score; **optionally** a supervised classifier (e.g. gradient boosting) trained on the generator's labels. The ML score feeds the v3 risk score. `scan --ml`.
- **Works.** Detection improves on subtle cases; measured against the labels, ML adds recall and/or cuts false positives versus rules-only.
- **Retained gaps.** Model is trained on synthetic data (note it honestly); not online/updating.
- **Test.** Train on a split of generated data, evaluate on a held-out split; report precision/recall/F1 and false-positive rate, and **compare rules-only vs. rules+ML** to show the lift. Confirm the model isn't trivially overfit (sane feature importances).
- **Decisions.** Isolation Forest first (versus deep learning) — strong, standard, CPU-friendly for tabular anomalies, and explainable enough. Supervised classifier optional because real fraud labels are scarce; showing both unsupervised and supervised is a strong story.

### v6 — LLM explanations (AI core #2)
- **Goal.** Explain every flag in plain English — the differentiator over a plain rule engine.
- **Adds.** For each flagged item, assemble the evidence (which rules fired, behavioral deviations, ML signal, the transaction itself) and prompt the LLM (Groq, OpenAI-compatible, model in config) to produce a concise explanation and a suggested analyst action. `scan --explain`.
- **Works.** Each high-risk flag carries a sentence a human immediately understands — e.g. "30 transfers just under ₹50k to new payees within an hour, consistent with structuring."
- **Retained gaps.** Explanations cost an API call each (so explain only flagged items, not every transaction); quality depends on the evidence you pass.
- **Test.** Confirm explanations are accurate to the actual signals (no invented reasons), concise, and useful. Confirm the model ID lives in config and a model swap needs no code change.
- **Decisions.** LLM explains, never detects (restated) — it reads the deterministic evidence and verbalizes it. Explanations generated only for flagged items (versus all) to bound cost.

### v7 — API layer
- **Goal.** Expose the results so a frontend (or any client) can consume them.
- **Adds.** FastAPI endpoints: list flagged transactions (filter by severity, account, date; sort by score), get one transaction's full detail (signals + explanation), list scan-run summaries, and trigger a scan. OpenAPI docs auto-generated.
- **Works.** Everything the CLI shows is now available over HTTP as clean JSON; you can drive the system without the terminal.
- **Retained gaps.** No auth yet (fine for local/demo; add a simple key at deploy); read-mostly.
- **Test.** Hit each endpoint; confirm the JSON matches what the CLI computes. Confirm filtering/sorting/pagination behave. OpenAPI docs load.
- **Decisions.** FastAPI (versus serving HTML from Python) — a clean JSON API is what the Next.js dashboard needs and is itself a strong backend artifact.

### v8 — Evaluation harness + scorecard (the proof)
- **Goal.** Prove the system works, with numbers.
- **Adds.** `evaluate` — runs the full pipeline on generated data with known labels and reports the scorecard: precision, recall, F1, false-positive rate, detection-rate by anomaly type (structuring vs. velocity vs. …), throughput (transactions/sec), and the **rules-only vs. rules+ML** comparison.
- **Works.** You have a reproducible, honest accuracy report — the centerpiece of the résumé/interview story.
- **Retained gaps.** Numbers are on synthetic data (state this plainly; it's standard and still meaningful).
- **Test.** Run it; confirm metrics are computed correctly against the labels (sanity-check precision/recall by hand on a tiny set). Confirm results are stable across seeds.
- **Decisions.** A dedicated harness (versus eyeballing) — "94% recall at 6% false-positive rate, a 70% false-positive reduction over rules alone" is the sentence that lands, and it must be real.

### Stage 2 — The dashboard (v9–v11)

### v9 — Next.js dashboard skeleton
- **Goal.** A real web UI showing flagged transactions from the API.
- **Adds.** A Next.js (App Router) + TypeScript + Tailwind app; a flagged-transactions table fetched from the v7 API (severity, score, account, amount, date), sortable and filterable; a clean layout.
- **Works.** Open the browser, see the ranked list of flagged transactions from real backend data.
- **Retained gaps.** Table only — no detail view, charts, or polish yet.
- **Test.** The table renders live API data; sorting/filtering work; empty and loading states behave.
- **Decisions.** Next.js/TS to match the target design quality (and Vercel deployment); table-first so the most important view exists before polish.

### v10 — Dashboard depth
- **Goal.** Make it genuinely useful and demo-worthy.
- **Adds.** A transaction **detail view** (all signals + the LLM explanation + suggested action); summary cards (total flagged, by severity); **charts** (flags over time, by anomaly type, score distribution) via Recharts; an account drill-down (its transactions + behavioral baseline); filters (date range, severity, type).
- **Works.** You can click a flag, see exactly why it fired in plain English, and explore patterns across accounts and time — the screen-share demo.
- **Retained gaps.** Polish/responsive details ongoing; no live-streaming updates.
- **Test.** Detail view matches the API's signal/explanation data; charts match the underlying numbers; drill-down navigation works.
- **Decisions.** Lead the detail view with the LLM explanation — it's the differentiating "this is why" moment that makes the demo memorable.

### v11 — Deploy + hardening
- **Goal.** A live, shareable system and a clean repo.
- **Adds.** Frontend on **Vercel**; backend on a container host (Render/Railway/Fly.io free tier) with **Postgres** (swap from SQLite) and a simple API key; environment config; a README with the architecture, the scorecard, and a demo GIF/recording.
- **Works.** A live URL (or a one-command local run) plus a documented, reproducible repo.
- **Retained gaps.** Single-node, demo-scale by design.
- **Test.** Deployed dashboard talks to the deployed backend end to end; cold-start works; README steps reproduce a local run from scratch.
- **Decisions.** Deploy is optional-but-nice — for the self-hosted ML, a recorded demo + the scorecard is a complete story even without paying to host; a live link is a bonus, not a requirement.

---

## 6. Stack & free-tier notes

- **All ML runs on CPU** — Isolation Forest and the statistics are light; no GPU needed.
- **LLM via Groq** (free tier, OpenAI-compatible, fast). Model ID lives in config because Groq deprecates/renames models; explanations are generated only for flagged items to bound usage.
- **Storage:** SQLite for the entire local build (zero infra); Postgres (Supabase/Neon free tier) only at deploy.
- **Frontend:** Vercel free tier hosts Next.js trivially. **Backend:** a free-tier container host or local Docker.
- **Data:** generated locally — no data costs, no privacy issues.

## 7. The résumé numbers (instrument from v5)

- **Precision / recall / F1** on labeled synthetic anomalies.
- **False-positive rate** — the core operational pain (real teams drown in false alerts); show ML reducing it versus rules.
- **Detection-rate by pattern type** (structuring, velocity, dormant-account, geo, …).
- **Rules-only vs. rules+ML lift** — the headline comparison.
- **Throughput** — transactions/sec the pipeline processes.

## 8. Repository structure

```
transaction-aml-detection-system/
  backend/
    app/
      cli.py                 # Typer CLI (ingest, generate, scan, evaluate, report)
      config.py              # settings (DB, Groq model, thresholds, weights)
      ingest/
        loader.py  schema.py # read + normalize transactions
      generate/
        generator.py         # synthetic data + injected labeled anomalies
      pipeline/
        scan.py              # THE SPINE — orchestrates the scan path
      detect/
        rules.py             # rule engine (baseline)
        scorer.py            # risk score + severity + ranking
        profile.py           # per-account behavioral baselines
        ml.py                # Isolation Forest / optional classifier + features
        explain.py           # LLM explanation (Groq)
      storage/
        db.py  models.py     # SQLite/Postgres, transactions/runs/flags/audit
      api/
        main.py  routes.py   # FastAPI app + endpoints
      eval/
        harness.py           # precision/recall/F1, FP rate, rules-vs-ML
    tests/                   # one module per version's "Test" step
    pyproject.toml           # uv
  frontend/
    app/                     # Next.js App Router pages
    components/              # table, detail view, charts, cards
    lib/                     # API client (typed)
    package.json
  README.md                  # architecture, scorecard, demo
```

---

### Stage → version map

- **Backbone & data** → v0 (ingest/store/summary), v1 (labeled generator), §4.
- **Detection** → v2 (rules), v3 (scoring), v4 (behavioral), v5 (ML — AI core #1).
- **Explanation (AI core #2)** → v6 (LLM).
- **Serve** → v7 (API).
- **Proof / the numbers** → v8 (scorecard), §7.
- **Dashboard** → v9 (skeleton), v10 (depth), v11 (deploy).