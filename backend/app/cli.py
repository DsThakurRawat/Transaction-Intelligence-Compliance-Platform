from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.ingest.loader import ingest_csv
from app.storage.db import SessionLocal, init_db
from app.storage.queries import compute_summary

app = typer.Typer(help="Transaction-and-AML-Detection-System (v0)")
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


if __name__ == "__main__":
    app()
