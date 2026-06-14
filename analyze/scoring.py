from typing import List
from config import Settings
from store.models import Flag, Score

def determine_band(score: int, settings: Settings) -> str:
    if score < settings.scoring_band_low:
        return "low"
    elif score < settings.scoring_band_medium:
        return "medium"
    elif score < settings.scoring_band_high:
        return "high"
    else:
        return "critical"

def compute_transaction_score(flags: List[Flag], settings: Settings) -> int:
    """Compute capped weighted sum of rule weights from flags."""
    if not flags:
        return 0
    
    total_score = 0
    for flag in flags:
        weight = settings.scoring_rule_weights.get(flag.rule_name, 0)
        total_score += weight
        
    return min(100, total_score)

def score_transaction(transaction_id: str, account_id: str, flags: List[Flag], settings: Settings) -> Score:
    """Generate a Score object for a given transaction."""
    score_value = compute_transaction_score(flags, settings)
    band = determine_band(score_value, settings)
    return Score(
        transaction_id=transaction_id,
        account_id=account_id,
        score=score_value,
        band=band
    )
