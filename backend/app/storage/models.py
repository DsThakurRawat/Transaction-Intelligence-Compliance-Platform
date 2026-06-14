from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    # transaction_id is the primary key — duplicates are rejected at the DB
    # level, which is the backbone of idempotent ingestion.
    transaction_id: Mapped[str] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3))
    merchant: Mapped[str] = mapped_column(String)
    merchant_category: Mapped[str] = mapped_column(String(8))
    country: Mapped[str] = mapped_column(String(2))
    channel: Mapped[str] = mapped_column(String)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
