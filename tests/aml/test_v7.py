import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from core.store.models import Score, Explanation
from interface.api import app, get_db
from tests.aml.test_v2_and_v3 import db_session_factory, setup_data
from analyzers.aml.explain import generate_explanations
from core.config import get_settings

@pytest.fixture
def client(setup_data, db_session_factory):
    # Override the dependency to use our test DB session
    def override_get_db():
        with db_session_factory() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_stats(client):
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_analyzer" in data
    assert "by_band" in data

def test_get_findings(client):
    response = client.get("/findings?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    if len(data) > 0:
        assert "id" in data[0]
        assert "score" in data[0]

def test_get_top_findings_and_accounts(client):
    resp_tx = client.get("/findings/top?limit=3")
    assert resp_tx.status_code == 200
    assert len(resp_tx.json()) <= 3
    
    resp_acc = client.get("/accounts/top?limit=3")
    assert resp_acc.status_code == 200
    assert len(resp_acc.json()) <= 3

@patch('analyzers.aml.explain.Groq')
def test_get_finding_detail(MockGroq, client, setup_data, db_session_factory):
    # Mock Groq to generate an explanation
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"explanation": "This is highly suspicious.", "suggested_action": "escalate"}'))]
    mock_client.chat.completions.create.return_value = mock_response
    MockGroq.return_value = mock_client
    
    settings = get_settings()
    settings.groq_api_key = "fake-key"
    
    with db_session_factory() as session:
        # Run the new analyzer to generate a Finding instead of raw generate_explanations
        from analyzers.aml.analyzer import AMLAnalyzer
        analyzer = AMLAnalyzer()
        analyzer.run(session, {})
        
        # Get a finding
        from core.store.models import Finding
        finding = session.scalar(select(Finding).where(Finding.score >= settings.scoring_band_high).limit(1))
        
        if finding:
            f_id = finding.id
            
            response = client.get(f"/findings/{f_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == f_id
            assert data["score"] == finding.score
            assert data["band"] == finding.band
