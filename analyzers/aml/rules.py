from typing import List, Optional
from datetime import timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from decimal import Decimal
from core.store.models import Transaction, Flag, AccountBaseline
from core.config import get_settings, Settings

class RuleFlag:
    def __init__(self, rule_name: str, reason: str, severity: str):
        self.rule_name = rule_name
        self.reason = reason
        self.severity = severity

class Rule:
    name: str = "base_rule"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        raise NotImplementedError

class LargeAmountRule(Rule):
    name = "amount"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        if tx.currency == "INR" and tx.amount > Decimal(str(settings.rule_amount_threshold_inr)):
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} exceeds INR threshold {settings.rule_amount_threshold_inr}", severity="high")
        elif tx.currency != "INR" and tx.amount > Decimal(str(settings.rule_amount_threshold_usd)):
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} exceeds USD threshold {settings.rule_amount_threshold_usd}", severity="high")
        return None

class HighRiskMCCRule(Rule):
    name = "high_risk_mcc"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        if tx.merchant_category in settings.rule_high_risk_mcc:
            return RuleFlag(rule_name=self.name, reason=f"Transaction in high-risk merchant category: {tx.merchant_category}", severity="medium")
        return None

class OddHourRule(Rule):
    name = "odd_hour"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        # tx.timestamp is naive but representing local/system time from generator.
        start = settings.rule_odd_hour_start
        end = settings.rule_odd_hour_end
        hour = tx.timestamp.hour
        is_odd = (start <= hour <= end) if start <= end else (hour >= start or hour <= end)
        if is_odd:
            return RuleFlag(rule_name=self.name, reason=f"Transaction at odd hour: {hour}:00", severity="low")
        return None

class VelocityRule(Rule):
    name = "velocity"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        window_start = tx.timestamp - timedelta(minutes=settings.rule_velocity_window_minutes)
        
        # Note: Re-queries per tx; acceptable for v2.
        stmt = select(func.count()).select_from(Transaction).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp <= tx.timestamp,
            Transaction.timestamp >= window_start
        )
        count = session.scalar(stmt)
        
        if count >= settings.rule_velocity_count:
            return RuleFlag(rule_name=self.name, reason=f"{count} transactions within {settings.rule_velocity_window_minutes} minutes", severity="critical")
        return None

class StructuringRule(Rule):
    name = "structuring"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        window_start = tx.timestamp - timedelta(hours=settings.rule_structuring_window_hours)
        
        if tx.currency == "INR":
            threshold = settings.rule_structuring_threshold_inr
        else:
            threshold = settings.rule_structuring_threshold_usd
            
        # We look for transactions in the window that are 80% to 100% of the threshold
        # If there are >= 2 such transactions, we flag for structuring.
        stmt = select(func.count()).select_from(Transaction).where(
            Transaction.account_id == tx.account_id,
            Transaction.currency == tx.currency,
            Transaction.timestamp <= tx.timestamp,
            Transaction.timestamp >= window_start,
            Transaction.amount >= threshold * 0.80,
            Transaction.amount < threshold
        )
        count = session.scalar(stmt)
        
        if count >= 2:
            return RuleFlag(rule_name=self.name, reason=f"Structuring pattern: {count} transactions just under threshold within {settings.rule_structuring_window_hours}h", severity="critical")
        return None

class BehavioralRule(Rule):
    """Base class for context-aware rules that require a baseline."""
    
    def get_baseline(self, tx: Transaction, session: Session) -> Optional[AccountBaseline]:
        return session.scalar(
            select(AccountBaseline).where(AccountBaseline.account_id == tx.account_id)
        )

class AmountDeviationRule(BehavioralRule):
    name = "amount_deviation"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        baseline = self.get_baseline(tx, session)
        # Min history guard: skip if < 10 txs
        if not baseline or baseline.tx_count < 10:
            return None
            
        # Robust z-score using MAD: 0.6745 * (x - median) / MAD
        robust_z_score = 0.6745 * (float(tx.amount) - float(baseline.amount_median)) / float(baseline.amount_mad)
        
        # Flag if out of pattern (z > 3)
        if robust_z_score > 3.0:
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} deviates sharply from profile (robust z-score {robust_z_score:.2f})", severity="high")
        return None

class NewCountryRule(BehavioralRule):
    name = "new_country"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        baseline = self.get_baseline(tx, session)
        if not baseline or baseline.tx_count < 5: # Kept at 5 to match prior country_mismatch
            return None
            
        if tx.country not in baseline.seen_countries:
            return RuleFlag(rule_name=self.name, reason=f"Country {tx.country} not in account history", severity="high")
        return None

class NewMCCRule(BehavioralRule):
    name = "new_mcc"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        baseline = self.get_baseline(tx, session)
        if not baseline or baseline.tx_count < 10:
            return None
            
        if tx.merchant_category not in baseline.seen_mccs:
            return RuleFlag(rule_name=self.name, reason=f"MCC {tx.merchant_category} not in account history", severity="medium")
        return None

class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = [
            LargeAmountRule(),
            HighRiskMCCRule(),
            OddHourRule(),
            VelocityRule(),
            StructuringRule(),
            AmountDeviationRule(),
            NewCountryRule(),
            NewMCCRule()
        ]
        
    def evaluate_transaction(self, tx: Transaction, session: Session) -> List[Flag]:
        settings = get_settings()
        flags = []
        for rule in self.rules:
            result = rule.evaluate(tx, session, settings)
            if result:
                flag = Flag(
                    transaction_id=tx.transaction_id,
                    account_id=tx.account_id,
                    rule_name=result.rule_name,
                    reason=result.reason,
                    severity=result.severity
                )
                flags.append(flag)
        return flags

engine = RuleEngine()
