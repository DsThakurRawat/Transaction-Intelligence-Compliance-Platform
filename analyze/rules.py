from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from store.models import Transaction, Flag
from config import get_settings, Settings

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
        if tx.currency == "INR" and float(tx.amount) > settings.rule_amount_threshold_inr:
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} exceeds INR threshold {settings.rule_amount_threshold_inr}", severity="high")
        elif tx.currency != "INR" and float(tx.amount) > settings.rule_amount_threshold_usd:
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

class CountryMismatchRule(Rule):
    name = "country_mismatch"
    
    def evaluate(self, tx: Transaction, session: Session, settings: Settings) -> Optional[RuleFlag]:
        # Get count of previous transactions
        count_stmt = select(func.count()).select_from(Transaction).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp < tx.timestamp
        )
        prior_tx_count = session.scalar(count_stmt)
        
        # Require history to prevent false flags on new accounts
        if prior_tx_count < 5:
            return None
            
        stmt = select(Transaction.country).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp < tx.timestamp
        ).distinct()
        previous_countries = session.scalars(stmt).all()
        
        if tx.country not in previous_countries:
            return RuleFlag(rule_name=self.name, reason=f"Country mismatch: {tx.country} not in account history", severity="high")
        return None

class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = [
            LargeAmountRule(),
            HighRiskMCCRule(),
            OddHourRule(),
            VelocityRule(),
            StructuringRule(),
            CountryMismatchRule()
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
