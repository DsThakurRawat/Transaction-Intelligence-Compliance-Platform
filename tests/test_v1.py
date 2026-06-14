import pytest
from data.generator import generate_profiles, generate_normal_transactions
from data.anomalies import inject_anomalies

def build(seed: int):
    profiles = generate_profiles(100, seed)
    df_normal = generate_normal_transactions(profiles, 30, seed)
    df_final = inject_anomalies(df_normal, anomaly_rate=0.05, seed=seed)
    return df_final

def test_reproducibility():
    """Ensure exact same output when using the same seed."""
    df1 = build(42)
    df2 = build(42)
    assert df1.equals(df2), "Reproducibility broken: datasets do not exactly match for the same seed."

def test_anomaly_rate():
    """Ensure the anomaly rate aligns roughly with the targeted rate (including injected bursts)."""
    df = build(42)
    actual_rate = df['is_anomaly'].sum() / len(df)
    # Target was 0.05, we expect it to be near 0.05
    assert 0.04 < actual_rate < 0.06, f"Anomaly rate {actual_rate} is not within tolerance of 0.05"

def test_anomaly_types_present():
    """Ensure all anomaly types are successfully generated."""
    df = build(42)
    types = df['anomaly_type'].unique()
    assert 'large_amount' in types
    assert 'velocity_fraud' in types
    assert 'geo_anomaly' in types
    assert 'structuring' in types
