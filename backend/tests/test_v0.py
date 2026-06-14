from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.ingest.loader import ingest_csv
from app.storage.db import make_engine
from app.storage.models import Base
from app.storage.queries import compute_summary

SAMPLE = """transaction_id,account_id,timestamp,amount,currency,merchant,merchant_category,country,channel
t1,acc1,2026-01-05T10:15:00,1500.00,INR,Amazon,5999,IN,online
t2,acc1,2026-01-05T12:30:00,250.50,INR,Starbucks,5814,IN,pos
t3,acc2,2026-01-06T09:00:00,99000.00,USD,Apple,5732,US,online
t1,acc1,2026-01-05T10:15:00,1500.00,INR,Amazon,5999,IN,online
t6,acc3,2026-01-07T21:00:00,notanumber,INR,Glitch,5999,IN,online
"""


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with factory() as s:
        yield s


def _csv(tmp_path, text=SAMPLE):
    p = tmp_path / "s.csv"
    p.write_text(text)
    return p


def test_ingest_counts(session, tmp_path):
    r = ingest_csv(_csv(tmp_path), session)
    assert r.inserted == 3            # t1, t2, t3
    assert r.skipped_duplicate == 1   # the second t1
    assert r.skipped_invalid == 1     # t6 (amount = "notanumber")
    assert r.total_rows == 5


def test_idempotent_reingest(session, tmp_path):
    path = _csv(tmp_path)
    ingest_csv(path, session)
    r2 = ingest_csv(path, session)    # re-run the exact same file
    assert r2.inserted == 0           # nothing new
    assert r2.skipped_duplicate == 4  # t1, t2, t3, and the in-file dup t1
    assert r2.skipped_invalid == 1


def test_summary(session, tmp_path):
    ingest_csv(_csv(tmp_path), session)
    s = compute_summary(session)
    assert s.count == 3
    assert s.total_amount == Decimal("100750.50")  # 1500 + 250.50 + 99000
    assert s.earliest == datetime(2026, 1, 5, 10, 15)
    assert s.latest == datetime(2026, 1, 6, 9, 0)
    by_cur = {b.currency: (b.count, b.total) for b in s.by_currency}
    assert by_cur["INR"] == (2, Decimal("1750.50"))
    assert by_cur["USD"] == (1, Decimal("99000"))
