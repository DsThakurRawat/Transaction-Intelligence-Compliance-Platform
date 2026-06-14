import pytest
import os
import numpy as np
import pandas as pd
from sqlalchemy import select
from sklearn.model_selection import train_test_split

from store.models import Transaction, Score
from analyze.features import extract_features
from analyze.ml import EnsembleAnomalyDetector, evaluate_supervised
from analyze.baselines import compute_baselines
from tests.test_v2_and_v3 import db_session_factory, setup_data

def test_feature_correctness_and_no_leakage(setup_data, db_session_factory):
    """Ensure features extract properly without NaNs/infs and contain no target leakage."""
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    assert not df_features.empty
    
    # Check for leakage
    leakage_cols = ['is_anomaly', 'anomaly_type']
    for col in leakage_cols:
        assert col not in df_features.columns, f"Target leakage found: {col} in features!"
        
    # Check basic health
    assert not df_features.isnull().values.any(), "Found NaNs in feature matrix!"
    assert not df_features.isin([np.inf, -np.inf]).values.any(), "Found infs in feature matrix!"
    assert 'log_amount' in df_features.columns
    assert 'robust_z_score' in df_features.columns

def test_ml_lifecycle_and_graceful_degradation(setup_data, db_session_factory, tmp_path):
    """Test train, save, load, and graceful degradation."""
    model_path = str(tmp_path / "ensemble.joblib")
    
    # Graceful degradation (no model)
    loaded_empty = EnsembleAnomalyDetector.load(model_path)
    assert loaded_empty is None
    
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    # Train & Save
    detector = EnsembleAnomalyDetector(random_state=42)
    detector.train(df_features) # No labels
    detector.save(model_path)
    
    assert os.path.exists(model_path)
    
    # Load & Score
    loaded_model = EnsembleAnomalyDetector.load(model_path)
    assert loaded_model is not None
    preds = loaded_model.predict(df_features)
    
    assert len(preds) == len(df_features)
    assert preds.min() >= 0.0 and preds.max() <= 1.0

def test_evaluation_metrics_and_lift(setup_data, db_session_factory):
    """
    Test the supervised comparison, account-split leakage prevention,
    and measure operational lift (FPR reduction vs rules-only).
    """
    df_labels = setup_data # df_final with is_anomaly
    
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    # Merge labels to prepare for evaluation
    df_merged = df_features.merge(df_labels[['transaction_id', 'account_id', 'is_anomaly']], on=['transaction_id', 'account_id'])
    
    # Account-based train/test split to prevent baseline leakage
    accounts = df_merged['account_id'].unique()
    train_accs, test_accs = train_test_split(accounts, test_size=0.3, random_state=42)
    
    df_train = df_merged[df_merged['account_id'].isin(train_accs)]
    df_test = df_merged[df_merged['account_id'].isin(test_accs)]
    
    # Ensemble Lift Check on Test Set
    detector = EnsembleAnomalyDetector(random_state=42)
    detector.train(df_train, y_train=df_train['is_anomaly'])
    
    ensemble_probs = detector.predict(df_test)
    
    # Let's print individual member performance vs ensemble for the bake-off artifact
    iso_probs = detector.iso_scaler.transform(-detector.iso_forest.decision_function(df_test[detector.feature_columns]).reshape(-1, 1)).flatten()
    booster_probs = detector.booster.predict_proba(df_test[detector.feature_columns])[:, 1]
    
    from sklearn.metrics import average_precision_score
    print(f"Iso Forest PR-AUC: {average_precision_score(df_test['is_anomaly'], iso_probs):.3f}")
    print(f"Gradient Boosting PR-AUC: {average_precision_score(df_test['is_anomaly'], booster_probs):.3f}")
    print(f"Ensemble PR-AUC: {average_precision_score(df_test['is_anomaly'], ensemble_probs):.3f}")
    
    # Compare with Rule-Based Score
    # We will simulate the Rules Score by aggregating the rule engine output
    with db_session_factory() as session:
        scores = session.scalars(select(Score)).all()
        score_map = {s.transaction_id: s.score for s in scores}
        
    df_test['rule_score'] = df_test['transaction_id'].map(score_map).fillna(0)
    df_test['rule_is_anomaly'] = df_test['rule_score'] >= 50 # Let's say >= 50 is an anomaly
    df_test['ml_is_anomaly'] = ensemble_probs > 0.65
    
    # Combine rules + ML (simulate config weighting)
    # E.g. ml_ensemble adds 40 points to score
    df_test['combined_score'] = df_test['rule_score'] + df_test['ml_is_anomaly'] * 40
    df_test['combined_is_anomaly'] = df_test['combined_score'] >= 50
    
    true_anoms = df_test['is_anomaly'] == True
    true_normals = df_test['is_anomaly'] == False
    
    rules_recall = (df_test['rule_is_anomaly'] & true_anoms).sum() / true_anoms.sum() if true_anoms.sum() > 0 else 0
    rules_fpr = (df_test['rule_is_anomaly'] & true_normals).sum() / true_normals.sum() if true_normals.sum() > 0 else 0
    
    combined_recall = (df_test['combined_is_anomaly'] & true_anoms).sum() / true_anoms.sum() if true_anoms.sum() > 0 else 0
    combined_fpr = (df_test['combined_is_anomaly'] & true_normals).sum() / true_normals.sum() if true_normals.sum() > 0 else 0
    
    print(f"Rules: Recall {rules_recall:.3f}, FPR {rules_fpr:.3f}")
    print(f"Combined (Rules+ML): Recall {combined_recall:.3f}, FPR {combined_fpr:.3f}")
    
    # Supervised harness
    metrics = evaluate_supervised(
        df_train.drop(columns=['is_anomaly', 'rule_score', 'rule_is_anomaly', 'ml_is_anomaly', 'combined_score', 'combined_is_anomaly'], errors='ignore'),
        df_test.drop(columns=['is_anomaly', 'rule_score', 'rule_is_anomaly', 'ml_is_anomaly', 'combined_score', 'combined_is_anomaly'], errors='ignore'),
        df_train['is_anomaly'],
        df_test['is_anomaly']
    )
    
    print(f"Supervised RF Metrics: {metrics}")
    
    assert metrics["pr_auc"] > 0.1, f"PR-AUC is extremely low: {metrics['pr_auc']}"
    # Ensure no plain accuracy is being used here since classes are heavily imbalanced.
