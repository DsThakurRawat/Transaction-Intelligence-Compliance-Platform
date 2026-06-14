import csv
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.schema import TransactionBase
from app.storage.models import Transaction


@dataclass
class IngestResult:
    inserted: int = 0
    skipped_duplicate: int = 0
    skipped_invalid: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)  # (line_no, message)

    @property
    def total_rows(self) -> int:
        return self.inserted + self.skipped_duplicate + self.skipped_invalid


def ingest_csv(path: Path, session: Session) -> IngestResult:
    """Read a CSV of transactions, validate each row, and insert new ones.

    Idempotent: a transaction_id already in the DB (or repeated within the
    file) is skipped, not duplicated. Invalid rows are skipped and counted.
    """
    result = IngestResult()

    # Existing IDs in the DB, so re-ingesting the same file is a no-op.
    existing: set[str] = set(session.scalars(select(Transaction.transaction_id)).all())
    seen_in_file: set[str] = set()
    to_add: list[Transaction] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            try:
                txn = TransactionBase(**row)
            except ValidationError as exc:
                result.skipped_invalid += 1
                msg = "; ".join(e["msg"] for e in exc.errors())
                result.errors.append((line_no, msg))
                continue

            if txn.transaction_id in existing or txn.transaction_id in seen_in_file:
                result.skipped_duplicate += 1
                continue

            seen_in_file.add(txn.transaction_id)
            to_add.append(Transaction(**txn.model_dump()))

    if to_add:
        session.add_all(to_add)
        session.commit()

    result.inserted = len(to_add)
    return result
