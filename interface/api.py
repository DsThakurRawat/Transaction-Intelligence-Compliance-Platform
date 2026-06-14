from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from typing import Optional, List
from datetime import datetime

from core.store.db import SessionLocal
from core.store.models import Finding

from pydantic import BaseModel

app = FastAPI(title="Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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

class FindingResponse(BaseModel):
    id: str
    analyzer: str
    entity_type: str
    entity_id: str
    finding_type: str
    score: Optional[float]
    band: Optional[str]
    status: str
    summary: str
    explanation: Optional[str]
    payload_json: Optional[dict]
    created_at: datetime

class StatsResponse(BaseModel):
    total: int
    by_analyzer: dict[str, int]
    by_band: dict[str, int]
    by_status: dict[str, int]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/findings", response_model=List[FindingResponse])
def get_findings(
    analyzer: Optional[str] = None,
    band: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    stmt = select(Finding).order_by(desc(Finding.created_at))
    if analyzer:
        stmt = stmt.where(Finding.analyzer == analyzer)
    if band:
        stmt = stmt.where(Finding.band == band)
    if status:
        stmt = stmt.where(Finding.status == status)
        
    findings = db.scalars(stmt.offset(offset).limit(limit)).all()
    
    return [FindingResponse(
        id=f.id,
        analyzer=f.analyzer,
        entity_type=f.entity_type,
        entity_id=f.entity_id,
        finding_type=f.finding_type,
        score=float(f.score) if f.score else None,
        band=f.band,
        status=f.status,
        summary=f.summary,
        explanation=f.explanation,
        payload_json=f.payload_json,
        created_at=f.created_at
    ) for f in findings]

@app.get("/findings/top", response_model=List[FindingResponse])
def get_top_findings(limit: int = 10, db: Session = Depends(get_db)):
    stmt = select(Finding).order_by(desc(Finding.score)).limit(limit)
    findings = db.scalars(stmt).all()
    return [FindingResponse(
        id=f.id,
        analyzer=f.analyzer,
        entity_type=f.entity_type,
        entity_id=f.entity_id,
        finding_type=f.finding_type,
        score=float(f.score) if f.score else None,
        band=f.band,
        status=f.status,
        summary=f.summary,
        explanation=f.explanation,
        payload_json=f.payload_json,
        created_at=f.created_at
    ) for f in findings]

@app.get("/stats", response_model=StatsResponse)
def get_finding_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Finding.id)))
    by_analyzer = dict(db.execute(select(Finding.analyzer, func.count(Finding.id)).group_by(Finding.analyzer)).all())
    
    # Handle nullable band
    by_band_rows = db.execute(select(Finding.band, func.count(Finding.id)).group_by(Finding.band)).all()
    by_band = {r[0] if r[0] else "none": r[1] for r in by_band_rows}
    
    by_status = dict(db.execute(select(Finding.status, func.count(Finding.id)).group_by(Finding.status)).all())
    
    return StatsResponse(
        total=total or 0,
        by_analyzer=by_analyzer,
        by_band=by_band,
        by_status=by_status
    )

@app.get("/findings/{finding_id}", response_model=FindingResponse)
def get_finding_detail(finding_id: str, db: Session = Depends(get_db)):
    f = db.scalar(select(Finding).where(Finding.id == finding_id))
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    return FindingResponse(
        id=f.id,
        analyzer=f.analyzer,
        entity_type=f.entity_type,
        entity_id=f.entity_id,
        finding_type=f.finding_type,
        score=float(f.score) if f.score else None,
        band=f.band,
        status=f.status,
        summary=f.summary,
        explanation=f.explanation,
        payload_json=f.payload_json,
        created_at=f.created_at
    )

@app.get("/accounts/top")
def api_get_top_accounts(limit: int = 10, db: Session = Depends(get_db)):
    from core.store.queries import get_top_accounts
    results = get_top_accounts(db, limit)
    return [
        {
            "account_id": r[0],
            "total_score": r[1],
            "critical_flags": r[2]
        } for r in results
    ]

@app.get("/graph")
def api_get_graph(limit: int = 500, db: Session = Depends(get_db)):
    from core.store.models import Score, Transaction
    scores = db.scalars(select(Score).order_by(desc(Score.score)).limit(limit)).all()
    
    nodes_map = {}
    edges = []
    
    for s in scores:
        tx = db.scalar(select(Transaction).where(Transaction.transaction_id == s.transaction_id))
        if tx and tx.counterparty_account:
            nodes_map[tx.account_id] = max(nodes_map.get(tx.account_id, 0), s.score)
            nodes_map[tx.counterparty_account] = max(nodes_map.get(tx.counterparty_account, 0), s.score / 2)
            
            edges.append({
                "source": tx.account_id,
                "target": tx.counterparty_account,
                "amount": float(tx.amount),
                "transaction_id": tx.transaction_id
            })
            
    nodes = [
        {
            "id": acc_id,
            "score": score,
            "risk_band": "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 30 else "low"
        }
        for acc_id, score in nodes_map.items()
    ]
    
    return {"nodes": nodes, "edges": edges}
