import json
import re
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config import settings

def _heuristic_intent_extractor(user_query: str) -> Dict[str, Any]:
    """Rule-based heuristic extraction fallback when Groq LLM is unreachable."""
    q = user_query.strip()
    
    # Extract cities
    from_city = None
    to_city = None
    route_match = re.search(r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+under|\s+starting|\s+reach|\s+with|\s*$|,)", q, re.IGNORECASE)
    if route_match:
        from_city = route_match.group(1).strip().title()
        to_city = route_match.group(2).strip().title()
    else:
        cities = re.findall(r"\b([A-Z][a-z]+)\b", q)
        if len(cities) >= 2:
            from_city = cities[0]
            to_city = cities[1]

    # Extract passengers
    passengers = 1
    p_match = re.search(r"(\d+)\s*(?:people|persons|passengers|travelers|adults)", q, re.IGNORECASE)
    if p_match:
        passengers = int(p_match.group(1))

    # Extract budget
    budget = None
    b_match = re.search(r"(?:under|below|budget|within|max)?\s*(?:rs\.?|inr|₹)?\s*(\d{4,7})\s*(?:inr|rs|rupees)?", q, re.IGNORECASE)
    if b_match:
        budget = float(b_match.group(1))

    # Extract bus type
    bus_type = "AC Sleeper"
    if re.search(r"non-?ac", q, re.IGNORECASE):
        bus_type = "Non-AC Seater"
    elif re.search(r"sleeper", q, re.IGNORECASE):
        bus_type = "AC Sleeper"
    elif re.search(r"seater", q, re.IGNORECASE):
        bus_type = "AC Seater"

    # Extract arrival deadline
    arrival_deadline = None
    arr_match = re.search(r"(?:reach|arrive|before|by)\s*(\d{1,2}(?::\d{2})?)\s*(am|pm)?", q, re.IGNORECASE)
    if arr_match:
        raw_time = arr_match.group(1)
        ampm = (arr_match.group(2) or "").lower()
        if ":" in raw_time:
            hours, mins = map(int, raw_time.split(":"))
        else:
            hours, mins = int(raw_time), 0
        if ampm == "pm" and hours < 12:
            hours += 12
        elif ampm == "am" and hours == 12:
            hours = 0
        arrival_deadline = f"{hours:02d}:{mins:02d}"

    # Default travel date: upcoming Friday
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    default_date = (today + timedelta(days=days_until_friday)).strftime("%Y-%m-%d")

    return {
        "from_city": from_city or "Bangalore",
        "to_city": to_city or "Ooty",
        "travel_date": default_date,
        "passengers": passengers,
        "bus_type": bus_type,
        "arrival_deadline": arrival_deadline or "08:00",
        "total_budget": budget or (10000.0 * passengers),
        "currency": "INR"
    }

def extract_intent_with_groq(user_query: str) -> Dict[str, Any]:
    """Extract travel constraints from natural language query using Groq Cloud with heuristic fallback."""
    if not settings.GROQ_API_KEY.strip():
        return _heuristic_intent_extractor(user_query)

    system_prompt = (
        "You are an expert travel constraint extractor. Output ONLY a valid JSON object with keys: "
        '"from_city" (string), "to_city" (string), "travel_date" (YYYY-MM-DD string), '
        '"passengers" (integer >= 1), "bus_type" (e.g. "AC Sleeper"), "arrival_deadline" (HH:MM 24-hr or null), '
        '"total_budget" (numeric or null), "currency" ("INR"). '
        "Map regional names to official English city names."
    )

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'Extract travel intent: "{user_query}"'},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 200,
    }

    try:
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

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            # Normalize fields
            if not parsed.get("passengers"):
                parsed["passengers"] = 1
            if not parsed.get("currency"):
                parsed["currency"] = "INR"
            return parsed
    except Exception:
        return _heuristic_intent_extractor(user_query)
