import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from store.models import Score, Explanation
from tests.test_v2_and_v3 import db_session_factory, setup_data
from analyze.explain import generate_explanations
from config import get_settings
from analyze.baselines import compute_baselines

def test_explain_graceful_degradation(setup_data, db_session_factory):
    """Test that missing GROQ_API_KEY degrades gracefully without crashing."""
    settings = get_settings()
    settings.groq_api_key = None
    
    with db_session_factory() as session:
        # Should not crash, just return
        generate_explanations(session, settings)
        
        # Verify no explanations were created
        exps = session.scalars(select(Explanation)).all()
        assert len(exps) == 0

@patch('analyze.explain.Groq')
def test_explain_generation_and_idempotency(MockGroq, setup_data, db_session_factory):
    """Test that the LLM is called and explanations are saved for high scores."""
    
    # Mock Groq API
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"explanation": "This is highly suspicious.", "suggested_action": "escalate"}'))]
    mock_client.chat.completions.create.return_value = mock_response
    MockGroq.return_value = mock_client
    
    settings = get_settings()
    settings.groq_api_key = "fake-key"
    
    with db_session_factory() as session:
        # Run baselines
        compute_baselines(session)
        
        # Manually promote a score to high band to ensure it gets explained
        scores = session.scalars(select(Score).limit(2)).all()
        for s in scores:
            s.score = 95
            s.band = "critical"
        session.commit()
        
        generate_explanations(session, settings)
        
        exps = session.scalars(select(Explanation)).all()
        assert len(exps) >= 2 # Since we promoted 2 scores
        
        for exp in exps:
            assert exp.explanation == "This is highly suspicious."
            assert exp.suggested_action == "escalate"
            
        # Test idempotency
        generate_explanations(session, settings)
        exps_run_2 = session.scalars(select(Explanation)).all()
        
        # The number of explanations should be exactly the same as run 1
        assert len(exps) == len(exps_run_2)
