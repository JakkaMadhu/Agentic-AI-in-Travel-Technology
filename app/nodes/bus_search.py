from typing import Dict, Any
from app.core.state import TravelPlanState
from app.services.bus_repository import search_buses

def bus_search_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Search and filter candidate buses."""
    candidates = search_buses(
        from_city=state["from_city"],
        to_city=state["to_city"],
        bus_type=state.get("bus_type"),
        arrival_deadline=state.get("arrival_deadline"),
    )
    
    selected = candidates[0] if candidates else None
    alternatives = candidates[1:] if len(candidates) > 1 else []
    return {
        "bus_candidates": candidates,
        "selected_bus": selected,
        "alternative_buses": alternatives
    }
