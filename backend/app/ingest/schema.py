from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TransactionBase(BaseModel):
    """The internal, normalized shape of a transaction. Everything downstream
    (rules, scoring, ML) reads this shape, regardless of the source format."""

    model_config = ConfigDict(str_strip_whitespace=True)

    transaction_id: str
    account_id: str
    timestamp: datetime
    amount: Decimal  # Decimal, not float — this is money. Negative = refund/credit.
    currency: str
    merchant: str
    merchant_category: str  # MCC; kept as str to preserve leading zeros
    country: str
    channel: str

    @field_validator("transaction_id", "account_id")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("currency")
    @classmethod
    def _currency_code(cls, v: str) -> str:
        v = v.upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return v

    @field_validator("country")
    @classmethod
    def _country_code(cls, v: str) -> str:
        v = v.upper()
        if len(v) != 2:
            raise ValueError("country must be a 2-letter ISO code")
        return v
