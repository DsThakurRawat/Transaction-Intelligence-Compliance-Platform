from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from typing import Optional, List
from datetime import datetime

from store.db import SessionLocal
from store.models import Transaction, Flag, Score, AccountBaseline, Explanation
from store.queries import get_top_transactions, get_top_accounts, compute_summary

from pydantic import BaseModel

app = FastAPI(title="AML Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class FlagResponse(BaseModel):
    rule_name: str
    reason: str
    severity: str
    
class ExplanationResponse(BaseModel):
    explanation: str
    suggested_action: str
    model_used: str

class BaselineResponse(BaseModel):
    tx_count: int
    amount_median: float
    amount_mad: float
    seen_countries: list[str]
    seen_mccs: list[str]

class TransactionListResponse(BaseModel):
    transaction_id: str
    account_id: str
    timestamp: datetime
    amount: float
    currency: str
    merchant: str
    score: int
    band: str
    flags: List[str]

class TransactionDetailResponse(BaseModel):
    transaction_id: str
    account_id: str
    timestamp: datetime
    amount: float
    currency: str
    merchant: str
    merchant_category: str
    country: str
    channel: str
    score: int
    band: str
    flags: List[FlagResponse]
    explanation: Optional[ExplanationResponse]
    baseline: Optional[BaselineResponse]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/transactions/flagged", response_model=List[TransactionListResponse])
def get_flagged_transactions(
    band: Optional[str] = None,
    account_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    stmt = select(Score).order_by(desc(Score.score))
    
    if band:
        stmt = stmt.where(Score.band == band)
    if account_id:
        stmt = stmt.where(Score.account_id == account_id)
        
    scores = db.scalars(stmt.offset(offset).limit(limit)).all()
    
    results = []
    for s in scores:
        tx = db.scalar(select(Transaction).where(Transaction.transaction_id == s.transaction_id))
        flags = db.scalars(select(Flag).where(Flag.transaction_id == s.transaction_id)).all()
        
        results.append(TransactionListResponse(
            transaction_id=s.transaction_id,
            account_id=s.account_id,
            timestamp=tx.timestamp,
            amount=float(tx.amount),
            currency=tx.currency,
            merchant=tx.merchant,
            score=int(s.score),
            band=s.band,
            flags=[f.rule_name for f in flags]
        ))
        
    return results

@app.get("/transactions/top")
def api_get_top_transactions(limit: int = 10, db: Session = Depends(get_db)):
    results = get_top_transactions(db, limit)
    return [
        {
            "transaction_id": r.transaction_id,
            "account_id": r.account_id,
            "score": int(r.score),
            "band": r.band
        } for r in results
    ]

@app.get("/accounts/top")
def api_get_top_accounts(limit: int = 10, db: Session = Depends(get_db)):
    results = get_top_accounts(db, limit)
    return [
        {
            "account_id": r[0],
            "total_score": r[1],
            "critical_flags": r[2]
        } for r in results
    ]

@app.get("/stats")
def api_get_stats(db: Session = Depends(get_db)):
    total_flagged = db.scalar(select(func.count(func.distinct(Flag.transaction_id))))
    
    rule_counts = dict(db.execute(
        select(Flag.rule_name, func.count()).group_by(Flag.rule_name)
    ).all())
    
    band_counts = dict(db.execute(
        select(Score.band, func.count()).group_by(Score.band)
    ).all())
    
    # Also get explanations count
    explanations_count = db.scalar(select(func.count()).select_from(Explanation))
    
    return {
        "total_flagged": total_flagged or 0,
        "by_rule": rule_counts,
        "by_band": band_counts,
        "explanations_generated": explanations_count or 0
    }

@app.get("/transactions/{transaction_id}", response_model=TransactionDetailResponse)
def get_transaction_detail(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    score = db.scalar(select(Score).where(Score.transaction_id == transaction_id))
    flags = db.scalars(select(Flag).where(Flag.transaction_id == transaction_id)).all()
    exp = db.scalar(select(Explanation).where(Explanation.transaction_id == transaction_id))
    baseline = db.scalar(select(AccountBaseline).where(AccountBaseline.account_id == tx.account_id))
    
    exp_resp = None
    if exp:
        exp_resp = ExplanationResponse(
            explanation=exp.explanation,
            suggested_action=exp.suggested_action,
            model_used=exp.model_used
        )
        
    base_resp = None
    if baseline:
        base_resp = BaselineResponse(
            tx_count=baseline.tx_count,
            amount_median=float(baseline.amount_median),
            amount_mad=float(baseline.amount_mad),
            seen_countries=baseline.seen_countries,
            seen_mccs=baseline.seen_mccs
        )
        
    return TransactionDetailResponse(
        transaction_id=tx.transaction_id,
        account_id=tx.account_id,
        timestamp=tx.timestamp,
        amount=float(tx.amount),
        currency=tx.currency,
        merchant=tx.merchant,
        merchant_category=tx.merchant_category,
        country=tx.country,
        channel=tx.channel,
        score=int(score.score) if score else 0,
        band=score.band if score else "none",
        flags=[FlagResponse(rule_name=f.rule_name, reason=f.reason, severity=f.severity) for f in flags],
        explanation=exp_resp,
        baseline=base_resp
    )
