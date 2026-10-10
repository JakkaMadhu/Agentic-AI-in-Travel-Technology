from typing import Dict, Any
from app.core.state import TravelPlanState
from app.services.rapidapi_client import fetch_live_hotels

def hotel_search_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Search and filter candidate hotels from Booking.com."""
    hotels = fetch_live_hotels(
        city_name=state["to_city"],
        max_budget=state.get("hotel_budget"),
        limit=5
    )

    selected = hotels[0] if hotels else None
    return {
        "hotel_candidates": hotels,
        "selected_hotel": selected
    }
