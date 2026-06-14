from sqlalchemy.orm import Session
from core.registry import get_analyzer
from core.store.models import AnalyzerRun
from datetime import datetime, timezone

def run_analyzer(name: str, session: Session, config: dict):
    analyzer = get_analyzer(name)
    
    # 1. Create run record
    run = AnalyzerRun(analyzer_name=name, started_at=datetime.now(timezone.utc), status="running")
    session.add(run)
    session.commit()
    
    try:
        # 2. Run analyzer
        result = analyzer.run(session, config)
        
        # 3. Complete run
        run.status = "completed"
        run.findings_count = result.findings_count
        run.message = result.message
        run.completed_at = datetime.now(timezone.utc)
        session.commit()
        return result
    except Exception as e:
        session.rollback()
        run.status = "failed"
        run.message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        session.commit()
        raise
