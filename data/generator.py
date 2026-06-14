import uuid
import random
from datetime import datetime, timedelta
from typing import List

import pandas as pd
import numpy as np
from pydantic import BaseModel

class AccountProfile(BaseModel):
    account_id: str
    country: str
    mean_amount: float
    std_amount: float
    merchant_categories: List[str]
    tx_rate: float
    currency: str

def get_random_merchant(mcc: str, country: str, py_rng: random.Random) -> str:
    return f"Merchant_{mcc}_{country}_{py_rng.randint(1, 100)}"

def generate_profiles(num_accounts: int, seed: int) -> List[AccountProfile]:
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    profiles = []
    countries = ["US", "IN", "GB", "CA", "AU", "DE", "FR"]
    currencies = {"US": "USD", "IN": "INR", "GB": "GBP", "CA": "CAD", "AU": "AUD", "DE": "EUR", "FR": "EUR"}
    mccs = ["5411", "5812", "5814", "5999", "5732", "5541"]
    
    for i in range(num_accounts):
        country = rng.choice(countries, p=[0.5, 0.2, 0.1, 0.05, 0.05, 0.05, 0.05])
        currency = currencies[country]
        mean_amount = rng.lognormal(mean=3.0, sigma=1.0)
        if currency == "INR":
            mean_amount *= 80
        std_amount = mean_amount * 0.5
        profile = AccountProfile(
            account_id=f"acc_{i:05d}",
            country=country,
            mean_amount=mean_amount,
            std_amount=std_amount,
            merchant_categories=py_rng.sample(mccs, k=py_rng.randint(2, 4)),
            tx_rate=rng.uniform(0.1, 3.0),
            currency=currency
        )
        profiles.append(profile)
    return profiles

def generate_normal_transactions(profiles: List[AccountProfile], days: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    # Fixed start date for reproducibility
    start_date = datetime(2026, 1, 1)
    
    rows = []
    for profile in profiles:
        num_tx = int(profile.tx_rate * days)
        # Compute underlying lognormal parameters given mean/std of amounts
        # var = std^2, log(1 + var / mean^2) is sigma^2 for underlying normal
        variance = profile.std_amount ** 2
        sigma2 = np.log(1 + variance / (profile.mean_amount ** 2))
        mu = np.log(profile.mean_amount) - (sigma2 / 2)
        sigma = np.sqrt(sigma2)
        
        for _ in range(num_tx):
            day_offset = py_rng.randint(0, days - 1)
            hour = int(rng.normal(loc=14, scale=4)) % 24
            minute = py_rng.randint(0, 59)
            tx_time = start_date + timedelta(days=day_offset, hours=hour, minutes=minute)
            
            amount = max(1.0, rng.lognormal(mean=mu, sigma=sigma))
            amount = round(amount, 2)
            mcc = py_rng.choice(profile.merchant_categories)
            
            rows.append({
                "transaction_id": str(uuid.UUID(int=py_rng.getrandbits(128))),
                "account_id": profile.account_id,
                "timestamp": tx_time,
                "amount": amount,
                "currency": profile.currency,
                "merchant": get_random_merchant(mcc, profile.country, py_rng),
                "merchant_category": mcc,
                "country": profile.country,
                "channel": py_rng.choice(["online", "pos"]),
                "is_anomaly": False,
                "anomaly_type": "none"
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("timestamp").reset_index(drop=True)
    return df
