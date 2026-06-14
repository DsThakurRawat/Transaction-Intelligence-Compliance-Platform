# Transactional & AML Detection System

A comprehensive system that monitors card-payment transactions and flags suspicious activity—detecting both **fraud** (single-transaction anomalies) and **AML / money-laundering patterns** (complex multi-transaction sequences like structuring). 

The detection engine combines a deterministic rule-engine with a **Machine Learning Ensemble** (Isolation Forest + LightGBM Booster) for risk scoring, leverages an LLM to generate plain-English explanations for analysts, and visualizes the risk topology on a Next.js 15+ interactive dashboard.

## Key Features

- **Hybrid Detection Engine**: Combines deterministic rules (velocity, structuring, odd-hours) with a machine learning ensemble. The ML ensemble provides a strong, defensible lift, correctly identifying multivariate anomalies that rigid rules miss.
- **Explainable AI (v6)**: Flags are interpreted by a large language model (Llama 3 via Groq), translating raw scores and rules into clear, actionable, plain-English summaries for analysts.
- **Interactive Network Graph (v12)**: The Next.js dashboard features an interactive force-directed graph to visualize counterparty money flows and high-risk clusters, making laundering rings immediately apparent.
- **Idempotent Ingestion Pipeline**: Powered by robust SQLAlchemy schemas and strict validation, ensuring clean data.

## Performance & Scorecard

By adding the ML ensemble, the system successfully bridges the detection gap by identifying multivariate and graphical structuring patterns without significantly spiking the false positive rate.

| Metric | Rules Only | Rules + ML Ensemble | Lift |
|--------|-------------------|--------------------------|------|
| **Recall** | 56.6% | 66.8% | **+10.2%** |
| **Precision** | 82.3% | 80.1% | -2.2% |
| **FPR** | 2.59% | 3.52% | +0.93% |
| **F1 Score** | 0.671 | 0.728 | +0.057 |
| **PR-AUC** | 0.697 | 0.741 | +0.044 |

*(Note: The ensemble adds substantial lift to Recall, pushing it above 66% with an honest tradeoff in precision—proving its value over rules alone.)*

## Architecture

- **Backend**: Python (FastAPI, Typer CLI, SQLAlchemy, Pandas, Scikit-Learn, LightGBM)
- **Frontend**: Next.js 15+, TailwindCSS, React Force Graph 2D
- **Database**: SQLite (local dev), easily swappable to PostgreSQL.

## How to Run

### 1. Backend CLI & API

```bash
# Sync dependencies
uv sync

# Generate synthetic data, ingest, train the ML model, and scan for fraud
PYTHONPATH=. uv run python interface/cli.py generate --accounts 200 --days 30
PYTHONPATH=. uv run python interface/cli.py ingest synthetic_data.csv
PYTHONPATH=. uv run python interface/cli.py train
PYTHONPATH=. uv run python interface/cli.py scan

# Run the FastAPI server
PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000
```

### 2. Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to see the "Quiet Instrument Panel" and Network Graph in action.

## Testing

```bash
# Run the evaluation test to generate the SCORECARD.md
uv run pytest tests/test_v8.py -s
```
