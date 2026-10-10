"""
Test 4B: Ultra-Fast Natural Language Parser via Groq Cloud
Model: llama-3.1-8b-instant (Fastest, zero 503 errors, 100% Free)
Project: AgenticTravelTech (TBS RoamAgent)
"""

import json
import os
import urllib.request
import env_loader

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions").strip()


def parse_travel_intent(user_query: str, api_key: str):
    """Uses Groq Cloud for sub-second travel constraint extraction."""
    system_prompt = (
        "You are a travel parameter extractor. Output ONLY a raw JSON object with keys: "
        '"from_city", "to_city", "arrival_deadline" (HH:MM 24-hr or null), "bus_type", "travel_date", "hotel_budget". '
        "Map regional names to official English city names (e.g., వైజాగ్ -> Visakhapatnam)."
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'Extract constraints: "{user_query}"'},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 120,
    }

    req = urllib.request.Request(
        GROQ_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
    except urllib.error.HTTPError as e:
        error_details = e.read().decode("utf-8")
        print(f"\n[HTTP Error {e.code} Details]:\n{error_details}")
        raise


if __name__ == "__main__":
    print("=" * 65)
    print("TEST 4B: GROQ ULTRA-FAST NLP PARSER (LLAMA 3.1 8B)")
    print("=" * 65)

    test_queries = [
        "Need an AC sleeper bus from Vizag to Hyderabad tomorrow before 8:30 AM",
        "నాకు రేపు రాత్రి వైజాగ్ నుండి హైదరాబాద్ స్లీపర్ బస్సు కావాలి, ఉదయం 8:30 లోపు చేరాలి",
    ]

    if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        print("\n[!] Please paste your Groq key on line 14 of this file.")
        print("Get your free key in 30 seconds at: https://console.groq.com/keys\n")
    else:
        for q in test_queries:
            print(f'\nParsing Query: "{q}"')
            try:
                extracted = parse_travel_intent(q, GROQ_API_KEY)
                print("Extracted Parameters:")
                print(json.dumps(extracted, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error: {e}")
            print("-" * 65)
