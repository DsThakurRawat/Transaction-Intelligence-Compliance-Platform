import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding
from core.config import get_settings
from analyzers.reporting.models import Report
from core.llm import get_groq_client
import json

class ReportingAnalyzer(Analyzer):
    name = "reporting"

    def required_inputs(self) -> list[str]:
        return ["findings"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # Clear drafts
        session.execute(delete(Report).where(Report.status == "draft"))
        session.commit()
        
        # Find all accounts with high/critical findings
        findings = session.scalars(select(Finding).where(Finding.band == "critical")).all()
        if not findings:
            return RunResult(0, "No critical findings to report")
            
        client = get_groq_client()
        if not client:
            return RunResult(0, "Groq client not available for SAR generation")
            
        reports_count = 0
        
        # Group by entity_id
        grouped = {}
        for f in findings:
            if f.entity_id not in grouped:
                grouped[f.entity_id] = []
            grouped[f.entity_id].append(f)
            
        for entity_id, entity_findings in grouped.items():
            if len(entity_findings) >= 2: # At least 2 critical findings
                evidence = [{"finding": f.summary, "score": float(f.score) if f.score else None, "type": f.finding_type} for f in entity_findings]
                
                prompt = f"""
                You are a compliance officer. Draft a Suspicious Activity Report (SAR) for the following entity.
                Entity ID: {entity_id}
                Evidence of Suspicion:
                {json.dumps(evidence, indent=2)}
                
                Keep the SAR brief, professional, and factual. Only use the provided evidence.
                """
                
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=settings.groq_model,
                        temperature=0.0
                    )
                    content = response.choices[0].message.content
                    
                    report = Report(
                        report_id=str(uuid.uuid4()),
                        entity_id=entity_id,
                        report_type="SAR",
                        status="draft",
                        content=content
                    )
                    session.add(report)
                    
                    finding = Finding(
                        id=str(uuid.uuid4()),
                        analyzer="reporting",
                        entity_type="report",
                        entity_id=report.report_id,
                        finding_type="sar_drafted",
                        score=100.0,
                        band="critical",
                        status="needs_review",
                        summary=f"SAR Drafted for entity {entity_id[:8]}",
                        payload_json={"report_id": report.report_id}
                    )
                    session.add(finding)
                    reports_count += 1
                except Exception as e:
                    pass
                    
        session.commit()
        return RunResult(reports_count, f"Drafted {reports_count} SARs")

    def evaluate(self, session: Session) -> Optional[str]:
        return None

register(ReportingAnalyzer())
