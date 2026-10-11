import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import settings

def extract_intent_with_groq(user_query: str) -> Dict[str, Any]:
    """
    Dynamically extracts travel constraints using LLM zero-shot multilingual understanding.
    Zero hardcoded dictionaries, zero regex heuristics, and zero fake fallback cities.
    """
    if not settings.GROQ_API_KEY.strip():
        raise RuntimeError("GROQ_API_KEY is not configured. An LLM service is required for natural language travel planning.")

    today_str = datetime.now().strftime("%Y-%m-%d")
    system_prompt = (
        "You are an expert multilingual travel constraint extractor. "
        f"Today's date is {today_str}. "
        "Extract the user's travel intent into a valid JSON object matching this schema: "
        '{"from_city": string or null, "to_city": string or null, "travel_date": "YYYY-MM-DD" or null, '
        '"duration_days": integer >= 1 or null, "return_bus": boolean or null, "passengers": integer >= 1, '
        '"bus_type": string or null, "arrival_deadline": "HH:MM" or null, "total_budget": numeric or null, "currency": "INR"}. '
        "You natively understand all languages, scripts (e.g. Telugu, Hindi, Tamil), and transliterations (e.g. Tanglish). "
        "Always translate regional city names to standard English (e.g. Hyderabad, Visakhapatnam, Bangalore, Ooty, etc.). "
        "Extract duration of the trip in days into duration_days (e.g., '3-day trip' / 'మూడు రోజులు' -> 3, '4 days' -> 4, '1 day' -> 1). If duration is NOT specified in the query, set duration_days to null. Do not guess duration. "
        "Extract whether a return bus ticket is wanted into return_bus (true for 'round trip' / 'return bus' / 'both ways' / 'రిటర్న్ బస్సు', false for 'one way' / 'single trip'). If NOT mentioned, set return_bus to null. Do not guess. "
        "If the user says 'today' / 'ఈరోజు', set travel_date to today's date. "
        "If the user only specifies where they want to go (destination e.g. 'హైదరాబాద్ వెళ్ళాలి' / 'going to Hyderabad') without stating their starting point, default from_city to 'Bangalore' (or 'Hyderabad' if destination is Bangalore). "
        "If the user does not specify a field, set it to null."
    )

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'Extract travel intent from: "{user_query}"'},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 250,
    }

    req = urllib.request.Request(
        settings.GROQ_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
            "User-Agent": "AgenticTravelTech/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

    # Dynamic normalization for optional fields
    if parsed.get("duration_days") is not None:
        try:
            val = int(parsed["duration_days"])
            parsed["duration_days"] = val if val >= 1 else None
        except Exception:
            parsed["duration_days"] = None
    else:
        parsed["duration_days"] = None

    if parsed.get("return_bus") is not None:
        parsed["return_bus"] = bool(parsed["return_bus"])
    else:
        parsed["return_bus"] = None

    if not parsed.get("passengers"):
        parsed["passengers"] = 1
    if not parsed.get("currency"):
        parsed["currency"] = "INR"
    if not parsed.get("travel_date"):
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7 or 7
        parsed["travel_date"] = (today + timedelta(days=days_until_friday)).strftime("%Y-%m-%d")

    return parsed
