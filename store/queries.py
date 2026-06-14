from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, case
from sqlalchemy.orm import Session
from store.models import Transaction, Score


@dataclass
class CurrencyBreakdown:
    currency: str
    count: int
    total: Decimal


@dataclass
class Summary:
    count: int
    total_amount: Decimal
    earliest: datetime | None
    latest: datetime | None
    by_currency: list[CurrencyBreakdown]


def compute_summary(session: Session) -> Summary:
    count = session.scalar(select(func.count()).select_from(Transaction)) or 0
    total = session.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0))
    )

    # Select the column itself (ordered) rather than func.min/max, so SQLAlchemy
    # returns a real datetime instead of a raw string from SQLite.
    earliest = session.scalar(
        select(Transaction.timestamp).order_by(Transaction.timestamp.asc()).limit(1)
    )
    latest = session.scalar(
        select(Transaction.timestamp).order_by(Transaction.timestamp.desc()).limit(1)
    )

    rows = session.execute(
        select(
            Transaction.currency,
            func.count(),
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .group_by(Transaction.currency)
        .order_by(Transaction.currency)
    ).all()
    by_currency = [
        CurrencyBreakdown(currency=c, count=n, total=Decimal(str(s))) for c, n, s in rows
    ]

    return Summary(
        count=count,
        total_amount=Decimal(str(total)),
        earliest=earliest,
        latest=latest,
        by_currency=by_currency,
    )

def get_top_transactions(session: Session, limit: int = 10) -> list[Score]:
    """Get the top riskiest transactions."""
    return session.scalars(
        select(Score).order_by(Score.score.desc()).limit(limit)
    ).all()

def get_top_accounts(session: Session, limit: int = 10) -> list[tuple[str, int, int]]:
    """
    Get the top riskiest accounts by computing the max score and counting critical flags.
    Returns list of tuples: (account_id, max_score, critical_count).
    """
    stmt = (
        select(
            Score.account_id,
            func.max(Score.score).label("max_score"),
            func.sum(
                case(
                    (Score.band == "critical", 1),
                    else_=0
                )
            ).label("critical_count")
        )
        .group_by(Score.account_id)
        .order_by(func.max(Score.score).desc())
        .limit(limit)
    )
    
    return session.execute(stmt).all()
