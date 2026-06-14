import json
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.store.models import Transaction, Flag, Score, AccountBaseline, Explanation
from core.config import Settings
import logging

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

def generate_explanations(session: Session, settings: Settings):
    """
    Generate LLM explanations for flagged transactions above the high severity band.
    Idempotent: deletes existing explanations before generating.
    Gracefully degrades if API key is missing or groq fails.
    """
    if not GROQ_AVAILABLE or not settings.groq_api_key:
        logger.warning("Groq API key not found or groq not installed. Skipping LLM explanations.")
        print("[yellow]Groq API key missing. Skipping LLM explanations.[/yellow]")
        return
        
    client = Groq(api_key=settings.groq_api_key)
    model = settings.groq_model
    
    # Idempotent clean
    session.execute(delete(Explanation))
    
    # Get all high/critical scores
    high_scores = session.scalars(
        select(Score).where(Score.score >= settings.scoring_band_high)
    ).all()
    
    if not high_scores:
        return
        
    for score_record in high_scores:
        tx_id = score_record.transaction_id
        
        # Assemble Evidence
        tx = session.scalar(select(Transaction).where(Transaction.transaction_id == tx_id))
        flags = session.scalars(select(Flag).where(Flag.transaction_id == tx_id)).all()
        baseline = session.scalar(select(AccountBaseline).where(AccountBaseline.account_id == score_record.account_id))
        
        evidence = {
            "transaction": {
                "amount": float(tx.amount),
                "currency": tx.currency,
                "merchant": tx.merchant,
                "country": tx.country,
                "channel": tx.channel
            },
            "risk_score": float(score_record.score),
            "severity_band": score_record.band,
            "fired_rules": [{"rule": f.rule_name, "reason": f.reason} for f in flags]
        }
        
        if baseline:
            evidence["account_baseline"] = {
                "median_amount": float(baseline.amount_median),
                "tx_count": baseline.tx_count,
                "known_countries": baseline.seen_countries
            }
            
        prompt = f"""
        You are an expert Anti-Money Laundering (AML) analyst.
        Review the following deterministic evidence for a flagged transaction and explain why it was flagged.
        
        Evidence:
        {json.dumps(evidence, indent=2)}
        
        Rules:
        1. Explain ONLY from the provided signals. Do not invent reasons.
        2. Keep it concise (2-3 sentences max).
        3. Provide a suggested action for the analyst (e.g., "monitor", "review", "escalate").
        4. Output strictly as JSON with exactly two keys: "explanation" and "suggested_action".
        """
        
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an AML explanation engine. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            output = response.choices[0].message.content
            parsed = json.loads(output)
            
            explanation_text = parsed.get("explanation", "Could not parse explanation.")
            action = parsed.get("suggested_action", "review")
            
            explanation_record = Explanation(
                transaction_id=tx_id,
                explanation=explanation_text,
                suggested_action=action,
                model_used=model
            )
            session.add(explanation_record)
            
        except Exception as e:
            logger.error(f"Error generating explanation for {tx_id}: {e}")
            
    session.commit()
