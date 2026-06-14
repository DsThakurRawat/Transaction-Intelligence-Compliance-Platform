import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select

from store.models import Transaction, Flag, AccountBaseline
from analyze.rules import engine as rule_engine
from analyze.baselines import compute_baselines
from store.db import make_engine, Base
from sqlalchemy.orm import sessionmaker
from config import get_settings

@pytest.fixture(scope="function")
def session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test_v4.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tx(session, account_id, tx_id, amount, country="US", mcc="5411", days_offset=0):
    tx = Transaction(
        transaction_id=tx_id,
        account_id=account_id,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_offset),
        amount=amount,
        currency="USD",
        merchant="Test Merchant",
        merchant_category=mcc,
        country=country,
        channel="online"
    )
    session.add(tx)
    return tx

def test_baseline_correctness(session_factory):
    with session_factory() as session:
        # Create 10 transactions with constant amount of 100 to check median and MAD
        for i in range(10):
            create_tx(session, "acc1", f"tx1_{i}", 100.0)
            
        # Create 10 transactions with increasing amounts: 10, 20, ..., 100
        for i in range(10):
            create_tx(session, "acc2", f"tx2_{i}", float((i+1)*10))
            
        session.commit()
        compute_baselines(session)
        
        # Check acc1 baseline
        b1 = session.scalar(select(AccountBaseline).where(AccountBaseline.account_id == "acc1"))
        assert b1 is not None
        assert b1.tx_count == 10
        assert b1.amount_median == Decimal("100.0")
        assert b1.amount_mad == Decimal("0.01") # Max(0, 0.01) guard
        
        # Check acc2 baseline
        b2 = session.scalar(select(AccountBaseline).where(AccountBaseline.account_id == "acc2"))
        assert b2 is not None
        # Values: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
        # Median = 55.0
        # MAD = median(|10-55|, ..., |100-55|) -> |45|, |35|, |25|, |15|, |5|, |5|, |15|, |25|, |35|, |45| -> Median = 25.0
        assert float(b2.amount_median) == 55.0
        assert float(b2.amount_mad) == 25.0

def test_context_awareness(session_factory):
    settings = get_settings()
    with session_factory() as session:
        # Low spender baseline (Median ~100)
        for i in range(10):
            create_tx(session, "low_acc", f"ltx_{i}", 100.0 + (i % 2)) # MAD will be ~0.5 (but bounded by 0.01 if constant, here it is 0.5)
            
        # High spender baseline (Median ~50000)
        for i in range(10):
            create_tx(session, "high_acc", f"htx_{i}", 50000.0 + (i % 2)*1000)
            
        session.commit()
        compute_baselines(session)
        
        # Test out-of-pattern transaction for low spender
        # Amount 2000 is far from median 100 (z-score > 3)
        tx_low_abnormal = create_tx(session, "low_acc", "ltx_abnormal", 2000.0)
        flags_low = rule_engine.evaluate_transaction(tx_low_abnormal, session)
        
        # Test same amount (2000) for high spender
        # Amount 2000 is much smaller than median 50000, not a large deviation spike upwards (well it might be a deviation downwards, but MAD is large so z-score might be small? Actually, z-score is absolute or directional?
        # The logic: robust_z_score = 0.6745 * (tx.amount - median) / MAD
        # If amount < median, z-score is negative, so it won't be > 3.0!
        tx_high_normal = create_tx(session, "high_acc", "htx_normal", 2000.0)
        flags_high = rule_engine.evaluate_transaction(tx_high_normal, session)
        
    assert any(f.rule_name == "amount_deviation" for f in flags_low), "Expected amount_deviation for low spender spike"
    assert not any(f.rule_name == "amount_deviation" for f in flags_high), "Did not expect amount_deviation for high spender normal transaction"

def test_minimum_history_guard(session_factory):
    settings = get_settings()
    with session_factory() as session:
        # Sparse account: only 3 transactions
        for i in range(3):
            create_tx(session, "sparse_acc", f"stx_{i}", 10.0)
            
        session.commit()
        compute_baselines(session)
        
        # Huge transaction that would normally be flagged
        tx_spike = create_tx(session, "sparse_acc", "stx_spike", 90000.0)
        flags = rule_engine.evaluate_transaction(tx_spike, session)
        
    # Should not trigger amount_deviation because history < 10
    assert not any(f.rule_name == "amount_deviation" for f in flags), "Expected behavioral rules to skip sparse accounts"

def test_new_country_and_mcc(session_factory):
    settings = get_settings()
    with session_factory() as session:
        for i in range(10):
            create_tx(session, "acc_a", f"atx_{i}", 100.0, country="US", mcc="5411")
            
        session.commit()
        compute_baselines(session)
        
        # Normal tx
        tx_normal = create_tx(session, "acc_a", "atx_n", 100.0, country="US", mcc="5411")
        flags_n = rule_engine.evaluate_transaction(tx_normal, session)
        
        # Abnormal tx
        tx_abnormal = create_tx(session, "acc_a", "atx_abn", 100.0, country="JP", mcc="5999")
        flags_abn = rule_engine.evaluate_transaction(tx_abnormal, session)
        
    assert not any(f.rule_name == "new_country" for f in flags_n)
    assert not any(f.rule_name == "new_mcc" for f in flags_n)
    
    assert any(f.rule_name == "new_country" for f in flags_abn)
    assert any(f.rule_name == "new_mcc" for f in flags_abn)
