from typing import Dict, Any
from app.core.state import TravelPlanState
from app.services.bus_repository import search_buses
from app.services.wiki_client import get_bus_route_distance_and_coords

def bus_search_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Search and filter candidate buses with road distance and coordinates."""
    from_city = state["from_city"]
    to_city = state["to_city"]

    # Calculate dynamic route distance and coordinates
    route_info = get_bus_route_distance_and_coords(from_city, to_city)
    dist_km = route_info.get("distance_km")
    fwd_origin = route_info.get("origin_coords")
    fwd_dest = route_info.get("destination_coords")

    candidates = search_buses(
        from_city=from_city,
        to_city=to_city,
        bus_type=state.get("bus_type"),
        arrival_deadline=state.get("arrival_deadline"),
    )

    for c in candidates:
        c["distance_km"] = dist_km
        c["origin_coords"] = fwd_origin
        c["destination_coords"] = fwd_dest
    
    selected = candidates[0] if candidates else None
    alternatives = candidates[1:] if len(candidates) > 1 else []

    # If return bus is required, search return buses (to_city -> from_city)
    return_required = state.get("return_bus_required")
    if return_required is None:
        return_required = True

    return_candidates = []
    selected_return = None
    alt_return = []

    if return_required:
        return_candidates = search_buses(
            from_city=to_city,
            to_city=from_city,
            bus_type=state.get("bus_type"),
            arrival_deadline=None,
        )
        for rc in return_candidates:
            rc["distance_km"] = dist_km
            rc["origin_coords"] = fwd_dest
            rc["destination_coords"] = fwd_origin

        selected_return = return_candidates[0] if return_candidates else None
        alt_return = return_candidates[1:] if len(return_candidates) > 1 else []

    return {
        "bus_candidates": candidates,
        "selected_bus": selected,
        "alternative_buses": alternatives,
        "return_bus_candidates": return_candidates,
        "selected_return_bus": selected_return,
        "alternative_return_buses": alt_return
    }
