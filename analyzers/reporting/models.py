from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from core.store.models import Base

class Report(Base):
    __tablename__ = "reports"
    
    report_id: Mapped[str] = mapped_column(String, primary_key=True)
    entity_id: Mapped[str] = mapped_column(String, index=True) # Usually an account ID
    report_type: Mapped[str] = mapped_column(String) # SAR
    status: Mapped[str] = mapped_column(String, default="draft") # draft, filed, rejected
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    filed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Filing(Base):
    __tablename__ = "filings"
    
    filing_id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(String, index=True)
    agency: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    filed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
