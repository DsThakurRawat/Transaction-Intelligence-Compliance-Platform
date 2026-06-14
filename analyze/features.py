import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select
from store.models import Transaction, AccountBaseline

def extract_features(session: Session, transactions: list[Transaction] = None) -> pd.DataFrame:
    """
    Extracts engineered features for ML detection from a list of transactions.
    If no transactions provided, fetches all from DB.
    Merges with AccountBaseline to compute context-aware features.
    
    WARNING: Does not include target labels to prevent leakage.
    """
    if not transactions:
        transactions = session.scalars(select(Transaction)).all()
        
    if not transactions:
        return pd.DataFrame()

    # Build DataFrame of all transactions for vectorized graph/velocity features
    df_all = pd.DataFrame([{
        "transaction_id": t.transaction_id,
        "account_id": t.account_id,
        "merchant": t.merchant,
        "timestamp": t.timestamp,
        "amount": float(t.amount)
    } for t in transactions])
    
    # Graph features: Bipartite network (Account -> Merchant)
    account_fan_out = df_all.groupby('account_id')['merchant'].nunique().to_dict()
    merchant_fan_in = df_all.groupby('merchant')['account_id'].nunique().to_dict()
    
    # Precompute global median for peer/population comparison
    global_median = df_all['amount'].median() if not df_all.empty else 0.0

    # Load baselines
    baselines = session.scalars(select(AccountBaseline)).all()
    baseline_map = {b.account_id: b for b in baselines}
    
    features_list = []

    for tx in transactions:
        b = baseline_map.get(tx.account_id)
        
        # Base features
        amount = float(tx.amount)
        log_amount = np.log1p(amount) # log1p handles amount 0 safely
        hour = tx.timestamp.hour
        day_of_week = tx.timestamp.weekday()
        
        # Context-aware features (default to 0/False if no baseline)
        if b and b.tx_count >= 10:
            robust_z = 0.6745 * (amount - float(b.amount_median)) / float(b.amount_mad)
            is_new_country = 1 if tx.country not in b.seen_countries else 0
            is_new_mcc = 1 if tx.merchant_category not in b.seen_mccs else 0
            tx_count = b.tx_count
        else:
            robust_z = 0.0
            is_new_country = 0
            is_new_mcc = 0
            tx_count = 0
            
        # Peer feature
        vs_global_median = amount / global_median if global_median > 0 else 0.0
        
        # Graph features
        fan_out = account_fan_out.get(tx.account_id, 0)
        fan_in = merchant_fan_in.get(tx.merchant, 0)
        
        features_list.append({
            "transaction_id": tx.transaction_id,
            "account_id": tx.account_id,
            "amount": amount,
            "log_amount": log_amount,
            "hour": hour,
            "day_of_week": day_of_week,
            "robust_z_score": robust_z,
            "is_new_country": is_new_country,
            "is_new_mcc": is_new_mcc,
            "tx_count": tx_count,
            "vs_global_median": vs_global_median,
            "account_fan_out": fan_out,
            "merchant_fan_in": fan_in,
            "channel": tx.channel,
            "mcc": tx.merchant_category
        })
        
    df = pd.DataFrame(features_list)
    
    # Categorical Encoding (One-Hot)
    # We strictly only one-hot encode. No target encoding to prevent leakage.
    df = pd.get_dummies(df, columns=["channel", "mcc"], drop_first=True)
    
    return df
