from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.storage.models import Transaction


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
