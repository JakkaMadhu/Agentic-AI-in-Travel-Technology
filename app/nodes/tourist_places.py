from typing import Dict, Any
from app.core.state import TravelPlanState
from app.services.wiki_client import fetch_city_attractions

def tourist_places_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Fetch city landmarks from MediaWiki."""
    attractions = fetch_city_attractions(city_name=state["to_city"], limit=4)
    return {
        "tourist_attractions": attractions
    }
