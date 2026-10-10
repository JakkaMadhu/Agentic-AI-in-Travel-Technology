import json
import urllib.request
from typing import Dict, Any
from app.config import settings

def extract_intent_with_groq(user_query: str) -> Dict[str, Any]:
    """Extract travel constraints from natural language query using Groq Cloud."""
    system_prompt = (
        "You are a travel parameter extractor. Output ONLY a raw JSON object with keys: "
        '"from_city", "to_city", "arrival_deadline" (HH:MM 24-hr or null), "bus_type", "travel_date", "hotel_budget" (numeric or null). '
        "Map regional names to official English city names (e.g., వైజాగ్ -> Visakhapatnam)."
    )

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'Extract constraints: "{user_query}"'},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 150,
    }

    req = urllib.request.Request(
        settings.GROQ_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgenticTravelTech/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
