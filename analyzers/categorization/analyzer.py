import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding, Transaction
from core.config import get_settings
from analyzers.categorization.models import TransactionCategory
from analyzers.categorization.engine import categorize_merchant

class CategorizationAnalyzer(Analyzer):
    name = "categorization"

    def required_inputs(self) -> list[str]:
        return ["transactions"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # 1. Clear prior state for idempotency
        session.execute(delete(Finding).where(Finding.analyzer == "categorization"))
        session.execute(delete(TransactionCategory))
        session.commit()
        
        transactions = session.scalars(select(Transaction)).all()
        if not transactions:
            return RunResult(0, "No transactions to categorize")
            
        findings_count = 0
        categories = []
        for tx in transactions:
            category, conf, source = categorize_merchant(tx.merchant)
            cat_obj = TransactionCategory(
                transaction_id=tx.transaction_id,
                category=category,
                confidence=conf,
                source=source
            )
            categories.append(cat_obj)
            
            # Emit finding for high-risk categories
            if category in ["crypto", "gambling"]:
                finding = Finding(
                    id=str(uuid.uuid4()),
                    analyzer="categorization",
                    entity_type="transaction",
                    entity_id=tx.transaction_id,
                    finding_type="high_risk_category",
                    score=80.0,
                    band="high",
                    status="open",
                    summary=f"Transaction assigned to high-risk category: {category}",
                    payload_json={"merchant": tx.merchant, "category": category, "confidence": conf}
                )
                session.add(finding)
                findings_count += 1
                
        session.add_all(categories)
        session.commit()
        
        return RunResult(findings_count, f"Categorized {len(transactions)} transactions, flagged {findings_count}")

    def evaluate(self, session: Session) -> Optional[str]:
        return None

register(CategorizationAnalyzer())
