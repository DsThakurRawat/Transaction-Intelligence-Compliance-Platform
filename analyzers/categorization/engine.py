import re
from typing import Tuple

RULES = [
    (re.compile(r'(?i)amazon|walmart|target|ebay'), "retail"),
    (re.compile(r'(?i)uber|lyft|taxi|transit|mta|airlines|delta|united'), "transportation"),
    (re.compile(r'(?i)starbucks|mcdonalds|restaurant|cafe|dining'), "food_and_dining"),
    (re.compile(r'(?i)netflix|spotify|hulu|apple|amzn'), "entertainment"),
    (re.compile(r'(?i)shell|chevron|exxon|gas'), "auto_and_transport"),
    (re.compile(r'(?i)pharmacy|cvs|walgreens|hospital'), "health_and_wellness"),
    (re.compile(r'(?i)coinbase|binance|kraken|crypto'), "crypto"), # High risk
    (re.compile(r'(?i)bet|casino|gambling|poker|draftkings'), "gambling"), # High risk
]

def categorize_merchant(merchant: str) -> Tuple[str, float, str]:
    """Returns (category, confidence, source)"""
    if not merchant:
        return ("unknown", 1.0, "regex")
        
    for pattern, category in RULES:
        if pattern.search(merchant):
            return (category, 0.9, "regex")
            
    return ("other", 0.5, "regex")
