import json
import os
from typing import List, Dict, Any, Optional
from app.config import settings

def load_bus_schedules() -> List[Dict[str, Any]]:
    """Load local bus timetable dataset."""
    if not os.path.exists(settings.BUSES_DATA_PATH):
        return []
    with open(settings.BUSES_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def search_buses(
    from_city: str,
    to_city: str,
    bus_type: Optional[str] = None,
    arrival_deadline: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Filter bus timetables by route, seating type, and arrival deadline."""
    buses = load_bus_schedules()
    matches = []

    for b in buses:
        # Route match (case insensitive)
        if b.get("from_city", "").lower() != from_city.lower():
            continue
        if b.get("to_city", "").lower() != to_city.lower():
            continue

        # Bus type filtering
        if bus_type:
            requested = bus_type.lower()
            available = b.get("bus_type", "").lower()
            if "sleeper" in requested and "sleeper" not in available:
                continue
            if "ac" in requested and "ac" not in available:
                continue

        # Arrival deadline filtering (HH:MM)
        if arrival_deadline:
            arr_time = b.get("arrival_time", "")
            if arr_time > arrival_deadline:
                continue

        matches.append(b)

    # Sort primarily by price ascending
    matches.sort(key=lambda x: x.get("fare_inr", 99999))
    return matches[:limit]
