from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from data.loader import ingest_csv
from store.db import SessionLocal, init_db
from data.generator import generate_profiles, generate_normal_transactions
from data.anomalies import inject_anomalies
from data.adapter import map_kaggle_dataset
from analyze.rules import engine as rule_engine
from analyze.scoring import score_transaction
from analyze.baselines import compute_baselines
from analyze.features import extract_features
from analyze.ml import EnsembleAnomalyDetector
from config import get_settings
from store.models import Transaction, Flag, Score
from store.queries import compute_summary, get_top_transactions, get_top_accounts
from sqlalchemy import select, delete

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
def scan() -> None:
    """Run rule-based detection on stored transactions and persist flags."""
    init_db()
    with SessionLocal() as session:
        # Clear prior flags and scores to ensure idempotency
        session.execute(delete(Flag))
        session.execute(delete(Score))
        
        # Get all transactions
        # In a real system, we'd paginate or filter by unscanned.
        stmt = select(Transaction).order_by(Transaction.timestamp)
        transactions = session.scalars(stmt).all()
        
        if not transactions:
            console.print("[yellow]No transactions to scan. Run `ingest` first.[/yellow]")
            return
            
        console.print("Phase 1/3: Computing per-account behavioral baselines...")
        compute_baselines(session)
        
        console.print("Phase 2/3: Loading ML model and computing batch features...")
        df_features = extract_features(session, transactions)
        detector = EnsembleAnomalyDetector.load()
        ml_flags = {}
        if detector and not df_features.empty:
            prob_series = detector.predict(df_features)
            for tx_id, prob in zip(df_features["transaction_id"], prob_series):
                if prob > 0.65: # High confidence threshold for flag
                    ml_flags[tx_id] = Flag(
                        transaction_id=tx_id,
                        account_id="", # Will be set below
                        rule_name="ml_ensemble",
                        reason=f"Transaction flagged by ML Ensemble (confidence: {prob:.2f})",
                        severity="high"
                    )
        else:
            console.print("[yellow]No ML model found or empty features. Degrading gracefully to rules-only mode.[/yellow]")
            
        settings = get_settings()
        console.print(f"Phase 3/3: Scanning {len(transactions)} transactions with rules...")
        
        total_flags = 0
        rule_counts = {}
        
        for tx in transactions:
            flags = rule_engine.evaluate_transaction(tx, session)
            if flags:
                # Add ml flag if exists
                ml_flag = ml_flags.get(tx.transaction_id)
                if ml_flag:
                    ml_flag.account_id = tx.account_id
                    flags.append(ml_flag)
                    
                session.add_all(flags)
                total_flags += len(flags)
                for f in flags:
                    rule_counts[f.rule_name] = rule_counts.get(f.rule_name, 0) + 1
                    
                score = score_transaction(tx.transaction_id, tx.account_id, flags, settings)
                session.add(score)
                    
            elif tx.transaction_id in ml_flags:
                # Only ML flagged it
                ml_flag = ml_flags[tx.transaction_id]
                ml_flag.account_id = tx.account_id
                flags = [ml_flag]
                session.add(ml_flag)
                total_flags += 1
                rule_counts["ml_ensemble"] = rule_counts.get("ml_ensemble", 0) + 1
                score = score_transaction(tx.transaction_id, tx.account_id, flags, settings)
                session.add(score)
                
        session.commit()
        
    console.print(f"[green]Scan complete! Generated {total_flags} flags.[/green]")
    if rule_counts:
        table = Table(title="Flags by Rule")
        table.add_column("Rule")
        table.add_column("Count", justify="right")
        for rule, count in rule_counts.items():
            table.add_row(rule, str(count))
        console.print(table)


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
def train() -> None:
    """Train the classical ML model (Isolation Forest) and persist it."""
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
    detector.train(df_features) # Unsupervised only in CLI
    detector.save()
    console.print("[green]Training complete. Model persisted to models/ensemble.joblib.[/green]")

if __name__ == "__main__":
    app()
