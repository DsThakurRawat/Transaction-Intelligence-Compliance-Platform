import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import select
from core.store.models import Finding
from core.config import get_settings
from analyzers.reporting.models import Report
from analyzers.reporting.analyzer import ReportingAnalyzer
from tests.aml.test_v2_and_v3 import db_session_factory

@patch('analyzers.reporting.analyzer.get_groq_client')
def test_reporting_analyzer(mock_get_client, db_session_factory):
    # Mock LLM
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='SAR Draft Content'))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    with db_session_factory() as session:
        # Create some critical findings
        f1 = Finding(id="f1", analyzer="aml", entity_type="transaction", entity_id="tx_1", finding_type="aml_alert", score=90, band="critical", status="open", summary="Test 1")
        f2 = Finding(id="f2", analyzer="reconciliation", entity_type="ledger_entry", entity_id="tx_1", finding_type="missing_processor", score=100, band="critical", status="open", summary="Test 2")
        session.add_all([f1, f2])
        session.commit()
        
        analyzer = ReportingAnalyzer()
        result = analyzer.run(session, {})
        
        assert result.findings_count == 1 # 1 SAR drafted for tx_1
        
        reports = session.scalars(select(Report)).all()
        assert len(reports) == 1
        assert reports[0].entity_id == "tx_1"
        assert reports[0].content == "SAR Draft Content"
