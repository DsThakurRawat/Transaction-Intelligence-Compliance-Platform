import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from core.store.models import Finding, Transaction
from analyzers.categorization.models import TransactionCategory
from analyzers.categorization.analyzer import CategorizationAnalyzer
from tests.aml.test_v2_and_v3 import db_session_factory

def test_categorization_analyzer(db_session_factory):
    with db_session_factory() as session:
        # Create dummy transactions
        tx1 = Transaction(
            transaction_id="tx_cat_1",
            account_id="acc_1",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("100.00"),
            currency="USD",
            merchant="Amazon",
            merchant_category="5411",
            country="US",
            channel="online"
        )
        tx2 = Transaction(
            transaction_id="tx_cat_2",
            account_id="acc_1",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("200.00"),
            currency="USD",
            merchant="Coinbase",
            merchant_category="6012",
            country="US",
            channel="online"
        )
        session.add_all([tx1, tx2])
        session.commit()
        
        analyzer = CategorizationAnalyzer()
        result = analyzer.run(session, {})
        
        assert result.findings_count == 1
        
        # Verify Categories
        cats = session.scalars(select(TransactionCategory)).all()
        assert len(cats) == 2
        
        cat_map = {c.transaction_id: c.category for c in cats}
        assert cat_map["tx_cat_1"] == "retail"
        assert cat_map["tx_cat_2"] == "crypto"
        
        # Verify Findings
        findings = session.scalars(select(Finding).where(Finding.analyzer == "categorization")).all()
        assert len(findings) == 1
        assert findings[0].entity_id == "tx_cat_2"
        assert findings[0].finding_type == "high_risk_category"
