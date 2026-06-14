import uuid
import random
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

def map_kaggle_dataset(input_csv: str, output_csv: str):
    """
    Maps the Kaggle Credit Card Fraud Detection dataset into our v0 schema.
    Keeps V1-V28 components for later ML validation (v5).
    """
    df = pd.read_csv(input_csv)
    
    # Kaggle schema: Time, V1-V28, Amount, Class
    base_time = datetime.now() - timedelta(days=365)
    
    print(f"Loaded {len(df)} rows from {input_csv}. Mapping...")
    
    # Vectorized mapping
    df['transaction_id'] = [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(len(df))]
    df['account_id'] = [f"real_{i:06d}" for i in range(len(df))] # Synthetic account to pass validation
    df['timestamp'] = base_time + pd.to_timedelta(df['Time'], unit='s')
    df['amount'] = df['Amount']
    df['currency'] = "USD"
    df['merchant'] = "Kaggle_Merchant"
    df['merchant_category'] = "0000"
    df['country'] = "US" # Must be 2-letter to pass validation
    df['channel'] = "online"
    
    df['is_anomaly'] = df['Class'].astype(bool)
    df['anomaly_type'] = np.where(df['is_anomaly'], 'real_fraud', 'none')
    
    cols_to_keep = [
        'transaction_id', 'account_id', 'timestamp', 'amount', 'currency',
        'merchant', 'merchant_category', 'country', 'channel',
        'is_anomaly', 'anomaly_type'
    ] + [f"V{i}" for i in range(1, 29)]
    
    out_df = df[cols_to_keep]
    out_df.to_csv(output_csv, index=False)
    print(f"Mapped dataset saved to {output_csv}")
