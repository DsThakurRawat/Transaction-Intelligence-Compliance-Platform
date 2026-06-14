from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, ForeignKey, UniqueConstraint, Integer, JSON
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
    counterparty_account: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

class Flag(Base):
    __tablename__ = "flags"
    __table_args__ = (UniqueConstraint('transaction_id', 'rule_name', name='uix_transaction_rule'),)
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String, ForeignKey("transactions.transaction_id"), index=True)
    account_id: Mapped[str] = mapped_column(String, index=True)
    rule_name: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

class Score(Base):
    __tablename__ = "scores"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String, ForeignKey("transactions.transaction_id"), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(String, index=True)
    score: Mapped[int] = mapped_column(Numeric(precision=3, scale=0))
    band: Mapped[str] = mapped_column(String)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

class AccountBaseline(Base):
    __tablename__ = "baselines"
    account_id: Mapped[str] = mapped_column(String, primary_key=True)
    tx_count: Mapped[int] = mapped_column(Integer)
    amount_median: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    amount_mad: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    seen_countries: Mapped[list[str]] = mapped_column(JSON)
    seen_mccs: Mapped[list[str]] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

class Explanation(Base):
    __tablename__ = "explanations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String, ForeignKey("transactions.transaction_id"), unique=True, index=True)
    explanation: Mapped[str] = mapped_column(String)
    suggested_action: Mapped[str] = mapped_column(String)
    model_used: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

# --- Platform Shared Models ---

class AnalyzerRun(Base):
    __tablename__ = "analyzer_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analyzer_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String) # running, completed, failed
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    findings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Finding(Base):
    __tablename__ = "findings"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # UUID
    analyzer: Mapped[str] = mapped_column(String, index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("analyzer_runs.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String) # e.g. transaction, account
    entity_id: Mapped[str] = mapped_column(String, index=True)
    finding_type: Mapped[str] = mapped_column(String)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    band: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open") # open, needs_review, resolved
    summary: Mapped[str] = mapped_column(String)
    explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    user: Mapped[str] = mapped_column(String, default="system")
    details: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
