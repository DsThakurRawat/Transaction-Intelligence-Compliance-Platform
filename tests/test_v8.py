import pytest
import os
import pandas as pd
import numpy as np
from sqlalchemy import select

from tests.test_v2_and_v3 import db_session_factory, setup_data
from analyze.evaluate import generate_scorecard
from analyze.features import extract_features
from analyze.ml import EnsembleAnomalyDetector
from analyze.baselines import compute_baselines

def test_generate_scorecard(setup_data, db_session_factory, tmp_path):
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    assert not df_features.empty
    
    df_merged = df_features.copy()
    df_merged = df_merged.merge(setup_data[['transaction_id', 'is_anomaly', 'anomaly_type']], on='transaction_id', how='left')
    
    # Split by account to prevent leakage
    accounts = df_merged['account_id'].unique()
    np.random.seed(42)
    np.random.shuffle(accounts)
    
    split_idx = int(len(accounts) * 0.8)
    train_accs = accounts[:split_idx]
    test_accs = accounts[split_idx:]
    
    df_train = df_merged[df_merged['account_id'].isin(train_accs)]
    df_test = df_merged[df_merged['account_id'].isin(test_accs)]
    
    # Train
    feature_cols = [c for c in df_features.columns]
    detector = EnsembleAnomalyDetector(random_state=42)
    detector.train(df_train[feature_cols], y_train=df_train['is_anomaly'])
    
    # Predict
    ensemble_probs = detector.predict(df_test[feature_cols])
    
    # Rules-only score from DB
    with db_session_factory() as session:
        from store.models import Score
        scores = session.scalars(select(Score)).all()
        score_map = {s.transaction_id: float(s.score) for s in scores}
        
    rules_scores = df_test['transaction_id'].map(score_map).fillna(0)
    ensemble_scores = rules_scores + (ensemble_probs > 0.65) * 40
    
    scorecard_path = "SCORECARD.md"
    md = generate_scorecard(df_test, rules_scores, ensemble_scores, output_path=scorecard_path)
    
    assert "Overall Performance Lift" in md
    assert os.path.exists(scorecard_path)
    
    # Read and print to verify
    print("\n" + md)
