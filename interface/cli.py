from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from core.ingest.loader import ingest_csv
from core.store.db import SessionLocal, init_db
from data.transactions import generate_profiles, generate_normal_transactions
from data.anomalies import inject_anomalies
from core.ingest.adapters import map_kaggle_dataset
from core.store.queries import compute_summary, get_top_transactions, get_top_accounts
from sqlalchemy import select, delete
from core.pipeline import run_analyzer
import analyzers.aml.analyzer
import analyzers.reconciliation.analyzer
import analyzers.categorization.analyzer
import analyzers.disputes.analyzer
import analyzers.reporting.analyzer

app = typer.Typer(help="Transaction-and-AML-Detection-System")
console = Console()


@app.command()
def ingest(
    file: Path = typer.Argument(..., exists=True, readable=True, help="CSV of transactions"),
) -> None:
    """Ingest a CSV of transactions into the local database."""
    init_db()
    with SessionLocal() as session:
        result = ingest_csv(file, session)

    table = Table(title="Ingest Result", show_header=False)
    table.add_row("Inserted", f"[green]{result.inserted}[/green]")
    table.add_row("Skipped (duplicate)", f"[yellow]{result.skipped_duplicate}[/yellow]")
    table.add_row("Skipped (invalid)", f"[red]{result.skipped_invalid}[/red]")
    table.add_row("Total rows read", str(result.total_rows))
    console.print(table)

    if result.errors:
        shown = result.errors[:5]
        console.print(f"[red]Invalid rows[/red] (showing {len(shown)} of {len(result.errors)}):")
        for line_no, msg in shown:
            console.print(f"  line {line_no}: {msg}")

@app.command()
def ingest_recon(
    num_records: int = typer.Option(1000, help="Number of records to generate"),
    anomaly_rate: float = typer.Option(0.05, help="Rate of discrepancies to inject"),
) -> None:
    """Generate and ingest synthetic ledger entries for reconciliation."""
    from data.reconciliation import generate_reconciliation_data
    from analyzers.reconciliation.models import LedgerEntry
    init_db()
    
    console.print(f"Generating {num_records} ledger entries with {anomaly_rate*100}% anomalies...")
    df = generate_reconciliation_data(num_records, anomaly_rate)
    
    with SessionLocal() as session:
        # Clear existing
        session.execute(delete(LedgerEntry))
        
        entries = []
        for _, row in df.iterrows():
            entry = LedgerEntry(
                id=row['id'],
                source=row['source'],
                external_ref=row['external_ref'],
                amount=row['amount'],
                currency=row['currency'],
                direction=row['direction'],
                transaction_date=row['transaction_date'],
                settlement_date=row['settlement_date'],
                status=row['status'],
                is_anomaly=row['is_anomaly'],
                anomaly_type=row['anomaly_type']
            )
            entries.append(entry)
            
        session.add_all(entries)
        session.commit()
        
    console.print(f"[green]Successfully ingested {len(entries)} ledger entries.[/green]")


@app.command()
def summary() -> None:
    """Print a summary of stored transactions."""
    init_db()
    with SessionLocal() as session:
        s = compute_summary(session)

    if s.count == 0:
        console.print("[yellow]No transactions stored yet. Run `ingest` first.[/yellow]")
        raise typer.Exit()

    overview = Table(title="Transaction Summary")
    overview.add_column("Metric")
    overview.add_column("Value", justify="right")
    overview.add_row("Total transactions", f"{s.count:,}")
    overview.add_row("Total amount", f"{s.total_amount:,.2f}")
    overview.add_row("Earliest", s.earliest.isoformat() if s.earliest else "-")
    overview.add_row("Latest", s.latest.isoformat() if s.latest else "-")
    console.print(overview)

    cur = Table(title="By Currency")
    cur.add_column("Currency")
    cur.add_column("Count", justify="right")
    cur.add_column("Total", justify="right")
    for b in s.by_currency:
        cur.add_row(b.currency, f"{b.count:,}", f"{b.total:,.2f}")
    console.print(cur)


@app.command()
def generate(
    accounts: int = typer.Option(100, help="Number of accounts to generate"),
    days: int = typer.Option(30, help="Number of days of transactions"),
    anomaly_rate: float = typer.Option(0.05, help="Target fraction of anomaly rows (e.g., 0.05 for 5%)"),
    seed: int = typer.Option(42, help="Random seed for reproducible generation"),
    out: Path = typer.Option(Path("synthetic_data.csv"), help="Output CSV path"),
) -> None:
    """Generate synthetic transactions with labeled anomalies."""
    console.print(f"Generating profiles for {accounts} accounts (seed={seed})...")
    profiles = generate_profiles(accounts, seed)
    
    console.print(f"Generating normal transactions over {days} days...")
    df_normal = generate_normal_transactions(profiles, days, seed)
    console.print(f"Generated {len(df_normal)} normal transactions.")
    
    console.print(f"Injecting anomalies (rate={anomaly_rate})...")
    df_final = inject_anomalies(df_normal, anomaly_rate, seed)
    
    num_anomalies = df_final['is_anomaly'].sum()
    console.print(f"Final dataset has {len(df_final)} rows ({num_anomalies} anomalies).")
    
    df_final.to_csv(out, index=False)
    console.print(f"[green]Saved synthetic dataset to {out}[/green]")


@app.command()
def import_real(
    input_csv: Path = typer.Argument(..., exists=True, readable=True, help="Kaggle creditcard.csv"),
    out: Path = typer.Option(Path("real_mapped_data.csv"), help="Output mapped CSV path"),
) -> None:
    """Adapt the Kaggle Credit Card Fraud dataset into our schema."""
    console.print(f"Mapping real dataset from {input_csv} to {out}...")
    map_kaggle_dataset(str(input_csv), str(out))
    console.print("[green]Mapping complete.[/green]")


@app.command()
def run(analyzer: str = typer.Argument(..., help="Name of the analyzer to run (e.g. 'aml')")) -> None:
    """Run an analyzer by name."""
    init_db()
    with SessionLocal() as session:
        try:
            console.print(f"Running analyzer '{analyzer}'...")
            result = run_analyzer(analyzer, session, {})
            console.print(f"[green]Analyzer completed: {result.message}[/green]")
        except KeyError:
            console.print(f"[red]Analyzer '{analyzer}' not found.[/red]")
        except Exception as e:
            console.print(f"[red]Error running analyzer: {str(e)}[/red]")


@app.command()
def top(
    limit: int = typer.Option(10, help="Number of results to display"),
) -> None:
    """Show the top riskiest transactions and accounts."""
    init_db()
    with SessionLocal() as session:
        top_txs = get_top_transactions(session, limit)
        top_accs = get_top_accounts(session, limit)
        
    console.print("\n[bold red]Top Riskiest Transactions[/bold red]")
    tx_table = Table(show_header=True)
    tx_table.add_column("Score", justify="right", style="cyan")
    tx_table.add_column("Band")
    tx_table.add_column("Account ID")
    tx_table.add_column("Transaction ID")
    
    for tx in top_txs:
        tx_table.add_row(str(tx.score), tx.band, tx.account_id, tx.transaction_id)
    console.print(tx_table)
    
    console.print("\n[bold red]Top Riskiest Accounts[/bold red]")
    acc_table = Table(show_header=True)
    acc_table.add_column("Account ID")
    acc_table.add_column("Max Score", justify="right", style="cyan")
    acc_table.add_column("Critical Flags", justify="right")
    
    for acc in top_accs:
        acc_table.add_row(acc[0], str(acc[1]), str(acc[2]))
    console.print(acc_table)

@app.command()
def train(
    labels_csv: Path = typer.Option(Path("synthetic_data.csv"), help="CSV with 'is_anomaly' labels for supervised training")
) -> None:
    """Train the classical ML model (Ensemble) and persist it."""
    init_db()
    with SessionLocal() as session:
        console.print("Fetching transactions and computing baselines...")
        compute_baselines(session)
        df_features = extract_features(session)
        
    if df_features.empty:
        console.print("[red]No transactions available for training.[/red]")
        return
        
    console.print(f"Training Ensemble Detector on {len(df_features)} transactions...")
    detector = EnsembleAnomalyDetector()
    
    y_train = None
    if labels_csv.exists():
        console.print(f"Loading labels from {labels_csv} for supervised training...")
        import pandas as pd
        df_labels = pd.read_csv(labels_csv)
        if 'transaction_id' in df_labels.columns and 'is_anomaly' in df_labels.columns:
            # Merge to align row order
            df_merged = df_features[['transaction_id']].merge(df_labels[['transaction_id', 'is_anomaly']], on='transaction_id', how='left')
            y_train = df_merged['is_anomaly'].fillna(False).astype(bool)
            console.print(f"Found {y_train.sum()} anomalies in labels. Booster will be enabled.")
        else:
            console.print("[yellow]Labels CSV missing 'transaction_id' or 'is_anomaly' columns. Falling back to unsupervised mode.[/yellow]")
            
    detector.train(df_features, y_train=y_train)
    detector.save()
    console.print("[green]Training complete. Model persisted to models/ensemble.joblib.[/green]")

@app.command()
def evaluate() -> None:
    """Run the offline evaluation harness and generate SCORECARD.md"""
    console.print("Running Evaluation Harness to generate SCORECARD.md...")
    import subprocess
    import sys
    
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/aml/test_v8.py", "-s", "-q"], capture_output=True, text=True)
    if result.returncode == 0:
        console.print("[green]Scorecard successfully generated at SCORECARD.md[/green]")
        try:
            with open("SCORECARD.md", "r") as f:
                console.print(f.read())
        except Exception:
            pass
    else:
        console.print("[red]Evaluation failed![/red]")
        console.print(result.stdout)
        console.print(result.stderr)


@app.command()
def findings(
    analyzer: str = typer.Option(None, help="Filter by analyzer name"),
    status: str = typer.Option(None, help="Filter by status (open, needs_review, resolved)"),
    limit: int = typer.Option(10, help="Number of findings to display"),
) -> None:
    """View the unified findings review queue."""
    from core.store.models import Finding
    init_db()
    with SessionLocal() as session:
        stmt = select(Finding).order_by(Finding.created_at.desc())
        if analyzer:
            stmt = stmt.where(Finding.analyzer == analyzer)
        if status:
            stmt = stmt.where(Finding.status == status)
            
        findings = session.scalars(stmt.limit(limit)).all()
        
    table = Table(title="Findings Review Queue")
    table.add_column("ID")
    table.add_column("Analyzer")
    table.add_column("Entity")
    table.add_column("Status")
    table.add_column("Score")
    table.add_column("Summary")
    
    for f in findings:
        table.add_row(
            f.id[:8],
            f.analyzer,
            f"{f.entity_type}:{f.entity_id[:8]}",
            f.status,
            f"{f.score:.0f}" if f.score else "-",
            f.summary
        )
    console.print(table)

if __name__ == "__main__":
    app()
