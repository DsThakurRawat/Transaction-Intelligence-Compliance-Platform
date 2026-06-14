from typing import Optional
from groq import Groq
from core.config import get_settings

_client: Optional[Groq] = None

def get_groq_client() -> Optional[Groq]:
    global _client
    settings = get_settings()
    if not settings.groq_api_key:
        return None
        
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client
