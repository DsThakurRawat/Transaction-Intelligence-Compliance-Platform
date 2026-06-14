import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import lightgbm as lgb

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "ensemble.joblib")

class EnsembleAnomalyDetector:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        
        # Member 1: Unsupervised
        self.iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.iso_scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Member 2: Supervised
        self.booster = lgb.LGBMClassifier(
            n_estimators=100,
            class_weight='balanced',
            random_state=self.random_state,
            n_jobs=-1,
            verbose=-1
        )
        
        self.feature_columns = None
        self.weights = {"iso": 1.0, "booster": 0.0} # Default to IF only if no labels

    def train(self, df_features: pd.DataFrame, y_train: pd.Series = None):
        X = df_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
        self.feature_columns = X.columns.tolist()
        
        # 1. Train Isolation Forest
        self.iso_forest.fit(X)
        # Fit scaler on raw anomaly scores (negative is more anomalous, so we negate)
        raw_iso_scores = -self.iso_forest.decision_function(X).reshape(-1, 1)
        self.iso_scaler.fit(raw_iso_scores)
        
        # 2. Train Booster if labels are available
        if y_train is not None:
            # Simple validation split to calculate PR-AUC weights
            X_t, X_v, y_t, y_v = train_test_split(X, y_train, test_size=0.2, random_state=self.random_state, stratify=y_train)
            
            self.booster.fit(X_t, y_t)
            
            # Evaluate Booster
            booster_preds_v = self.booster.predict_proba(X_v)[:, 1]
            booster_pr_auc = average_precision_score(y_v, booster_preds_v)
            
            # Evaluate Iso
            iso_raw_v = -self.iso_forest.decision_function(X_v).reshape(-1, 1)
            iso_preds_v = self.iso_scaler.transform(iso_raw_v).flatten()
            iso_pr_auc = average_precision_score(y_v, iso_preds_v)
            
            # Calculate weights based on PR-AUC
            total = booster_pr_auc + iso_pr_auc
            if total > 0:
                self.weights["iso"] = iso_pr_auc / total
                self.weights["booster"] = booster_pr_auc / total
            else:
                self.weights["iso"] = 0.5
                self.weights["booster"] = 0.5
                
            # Retrain booster on full data
            self.booster.fit(X, y_train)

    def predict(self, df_features: pd.DataFrame) -> pd.Series:
        X = df_features.copy()
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_columns]
        
        # Iso prediction [0, 1]
        raw_iso_scores = -self.iso_forest.decision_function(X).reshape(-1, 1)
        iso_scores = self.iso_scaler.transform(raw_iso_scores).flatten()
        
        # Combine
        final_scores = iso_scores * self.weights["iso"]
        
        if self.weights["booster"] > 0:
            booster_scores = self.booster.predict_proba(X)[:, 1]
            final_scores += booster_scores * self.weights["booster"]
            
        return pd.Series(final_scores, index=df_features.index)

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "iso_forest": self.iso_forest,
            "iso_scaler": self.iso_scaler,
            "booster": self.booster,
            "weights": self.weights,
            "features": self.feature_columns
        }, path)

    @classmethod
    def load(cls, path: str = MODEL_PATH):
        if not os.path.exists(path):
            return None
        
        data = joblib.load(path)
        detector = cls()
        detector.iso_forest = data["iso_forest"]
        detector.iso_scaler = data["iso_scaler"]
        detector.booster = data["booster"]
        detector.weights = data["weights"]
        detector.feature_columns = data["features"]
        return detector

def evaluate_supervised(df_train_features: pd.DataFrame, df_test_features: pd.DataFrame, y_train: pd.Series, y_test: pd.Series, random_state: int = 42):
    """
    Supervised comparison harness.
    Trains a Random Forest with class_weight='balanced_subsample' to handle the heavy imbalance.
    """
    X_train = df_train_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
    X_test = df_test_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
    
    # Align test features to train
    for col in X_train.columns:
        if col not in X_test.columns:
            X_test[col] = 0
    X_test = X_test[X_train.columns]

    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight='balanced_subsample',
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    return {
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_test, y_prob)
    }
