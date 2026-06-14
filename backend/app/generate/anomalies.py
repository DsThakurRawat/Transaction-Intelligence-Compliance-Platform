import uuid
import random
from datetime import timedelta

import pandas as pd
import numpy as np

def inject_fraud_large_amount(df: pd.DataFrame, index: int, py_rng: random.Random, multiplier: float = 20.0):
    df.at[index, 'amount'] = round(df.at[index, 'amount'] * multiplier, 2)
    df.at[index, 'is_anomaly'] = True
    df.at[index, 'anomaly_type'] = "large_amount"

def inject_fraud_velocity(df: pd.DataFrame, index: int, py_rng: random.Random) -> pd.DataFrame:
    base_row = df.iloc[index].copy()
    num_tx = py_rng.randint(5, 10)
    
    # Mutate the anchor row to be the first of the burst
    df.at[index, 'amount'] = round(py_rng.uniform(5.0, 50.0), 2)
    df.at[index, 'is_anomaly'] = True
    df.at[index, 'anomaly_type'] = "velocity_fraud"
    
    new_rows = []
    base_time = base_row['timestamp']
    for _ in range(num_tx - 1):
        new_row = base_row.copy()
        new_row['transaction_id'] = str(uuid.UUID(int=py_rng.getrandbits(128)))
        new_row['timestamp'] = base_time + timedelta(seconds=py_rng.randint(1, 300))
        new_row['amount'] = round(py_rng.uniform(5.0, 50.0), 2)
        new_row['is_anomaly'] = True
        new_row['anomaly_type'] = "velocity_fraud"
        new_rows.append(new_row)
    return pd.DataFrame(new_rows)

def inject_fraud_geo(df: pd.DataFrame, index: int):
    df.at[index, 'country'] = "RU"
    df.at[index, 'is_anomaly'] = True
    df.at[index, 'anomaly_type'] = "geo_anomaly"

def inject_aml_structuring(df: pd.DataFrame, index: int, py_rng: random.Random) -> pd.DataFrame:
    base_row = df.iloc[index].copy()
    if base_row['currency'] == "INR":
        threshold = 50000.0
    else:
        threshold = 10000.0
        
    num_tx = py_rng.randint(3, 5)
    # Generate amounts that are individually close to the reporting threshold
    amounts = [round(py_rng.uniform(threshold * 0.85, threshold * 0.99), 2) for _ in range(num_tx)]
    
    # Mutate the anchor row to be the first of the sequence
    df.at[index, 'amount'] = amounts[0]
    df.at[index, 'is_anomaly'] = True
    df.at[index, 'anomaly_type'] = "structuring"
    
    new_rows = []
    base_time = base_row['timestamp']
    for i in range(1, num_tx):
        new_row = base_row.copy()
        new_row['transaction_id'] = str(uuid.UUID(int=py_rng.getrandbits(128)))
        new_row['timestamp'] = base_time + timedelta(hours=py_rng.randint(1, 48))
        new_row['amount'] = amounts[i]
        new_row['is_anomaly'] = True
        new_row['anomaly_type'] = "structuring"
        new_rows.append(new_row)
    return pd.DataFrame(new_rows)

def inject_anomalies(df: pd.DataFrame, anomaly_rate: float, seed: int) -> pd.DataFrame:
    if df.empty:
        return df
        
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    
    target_anomaly_rows = int(len(df) * anomaly_rate)
    current_anomaly_rows = 0
    
    available_indices = list(range(len(df)))
    py_rng.shuffle(available_indices)
    
    extra_rows = []
    
    for idx in available_indices:
        if current_anomaly_rows >= target_anomaly_rows:
            break
            
        anomaly_type = py_rng.choice([
            "large_amount", "velocity_fraud", "geo_anomaly", "structuring"
        ])
        
        if anomaly_type == "large_amount":
            inject_fraud_large_amount(df, idx, py_rng)
            current_anomaly_rows += 1
        elif anomaly_type == "velocity_fraud":
            new_df = inject_fraud_velocity(df, idx, py_rng)
            extra_rows.append(new_df)
            current_anomaly_rows += len(new_df) + 1 # +1 for anchor row
        elif anomaly_type == "geo_anomaly":
            inject_fraud_geo(df, idx)
            current_anomaly_rows += 1
        elif anomaly_type == "structuring":
            new_df = inject_aml_structuring(df, idx, py_rng)
            extra_rows.append(new_df)
            current_anomaly_rows += len(new_df) + 1 # +1 for anchor row
            
    if extra_rows:
        df = pd.concat([df] + extra_rows, ignore_index=True)
        df = df.sort_values("timestamp").reset_index(drop=True)
        
    return df
