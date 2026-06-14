from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column
from core.store.models import Base

class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    
    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String) # regex, llm
