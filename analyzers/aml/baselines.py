import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from core.store.models import Transaction, AccountBaseline

def compute_baselines(session: Session) -> None:
    """
    Computes per-account behavioral baselines from all historical transactions
    using robust statistics (Median + MAD).
    """
    # 1. Idempotency: Clear existing baselines
    session.execute(delete(AccountBaseline))
    
    # 2. Fetch all transactions (in memory for pandas aggregation)
    # For massive production datasets, this would be a chunked or pure SQL operation
    stmt = select(Transaction.account_id, Transaction.amount, Transaction.country, Transaction.merchant_category)
    rows = session.execute(stmt).all()
    
    if not rows:
        return
        
    df = pd.DataFrame(rows, columns=['account_id', 'amount', 'country', 'merchant_category'])
    
    # Convert amounts to float for numpy ops
    df['amount'] = df['amount'].astype(float)
    
    # 3. Compute Median and MAD per account
    grouped = df.groupby('account_id')
    
    baselines = []
    for account_id, group in grouped:
        tx_count = len(group)
        amount_median = group['amount'].median()
        
        # MAD = median(|x_i - median(X)|)
        # Add a tiny epsilon to MAD to avoid division by zero later for constant-amount accounts
        amount_mad = (group['amount'] - amount_median).abs().median()
        amount_mad = max(amount_mad, 0.01) 
        
        # Robust sets: filter out one-offs that might be the anomaly itself
        country_counts = group['country'].value_counts()
        seen_countries = country_counts[country_counts > 1].index.tolist()
        if not seen_countries:
            seen_countries = group['country'].unique().tolist()
            
        mcc_counts = group['merchant_category'].value_counts()
        seen_mccs = mcc_counts[mcc_counts > 1].index.tolist()
        if not seen_mccs:
            seen_mccs = group['merchant_category'].unique().tolist()
        
        baselines.append(AccountBaseline(
            account_id=account_id,
            tx_count=tx_count,
            amount_median=amount_median,
            amount_mad=amount_mad,
            seen_countries=seen_countries,
            seen_mccs=seen_mccs
        ))
        
    session.add_all(baselines)
    session.commit()
