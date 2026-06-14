from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding
from core.store.models import Transaction, Flag, Score
from analyzers.aml.baselines import compute_baselines
from analyzers.aml.features import extract_features
from analyzers.aml.ml import EnsembleAnomalyDetector
from analyzers.aml.rules import engine as rule_engine
from analyzers.aml.scoring import score_transaction
from core.config import get_settings
import uuid

class AMLAnalyzer(Analyzer):
    name = "aml"

    def required_inputs(self) -> list[str]:
        return ["transactions"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # Clear prior state for idempotency (AML specific)
        session.execute(delete(Finding).where(Finding.analyzer == "aml"))
        session.execute(delete(Flag))
        session.execute(delete(Score))
        session.commit()
        
        # 1. Baselines
        compute_baselines(session)
        
        # 2. ML Batch Features
        transactions = session.scalars(select(Transaction).order_by(Transaction.timestamp)).all()
        if not transactions:
            return RunResult(0, "No transactions to scan")
            
        df_features = extract_features(session, transactions)
        detector = EnsembleAnomalyDetector.load()
        ml_flags = {}
        if detector and not df_features.empty:
            prob_series = detector.predict(df_features)
            for tx_id, prob in zip(df_features["transaction_id"], prob_series):
                if prob > 0.65:
                    ml_flags[tx_id] = Flag(
                        transaction_id=tx_id,
                        account_id="", # Handled later
                        rule_name="ml_ensemble",
                        reason=f"Transaction flagged by ML Ensemble (confidence: {prob:.2f})",
                        severity="high"
                    )
                    
        # 3. Rules & Scoring
        findings_count = 0
        for tx in transactions:
            flags = rule_engine.evaluate_transaction(tx, session)
            if tx.transaction_id in ml_flags:
                ml_flag = ml_flags[tx.transaction_id]
                ml_flag.account_id = tx.account_id
                flags.append(ml_flag)
                
            if flags:
                session.add_all(flags)
                score_obj = score_transaction(tx.transaction_id, tx.account_id, flags, settings)
                session.add(score_obj)
                
                # Create Finding
                if score_obj.score >= settings.scoring_band_low:
                    finding = Finding(
                        id=str(uuid.uuid4()),
                        analyzer="aml",
                        entity_type="transaction",
                        entity_id=tx.transaction_id,
                        finding_type="aml_alert",
                        score=score_obj.score,
                        band=score_obj.band,
                        status="needs_review" if score_obj.score >= settings.scoring_band_high else "open",
                        summary=f"AML Alert: {len(flags)} rules triggered",
                        payload_json={"flags": [f.rule_name for f in flags]}
                    )
                    session.add(finding)
                    findings_count += 1
                    
        session.commit()
            
        return RunResult(findings_count, f"Scanned {len(transactions)} txs, found {findings_count} anomalies")

    def evaluate(self, session: Session) -> Optional[str]:
        return None

register(AMLAnalyzer())
