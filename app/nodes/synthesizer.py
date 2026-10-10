import urllib.parse
from typing import Dict, Any
from app.core.state import TravelPlanState

def synthesizer_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Synthesize budget, compute totals, and formulate deep links."""
    selected_bus = state.get("selected_bus")
    selected_hotel = state.get("selected_hotel")
    hotel_budget = state.get("hotel_budget")

    bus_cost = float(selected_bus.get("fare_inr", 0)) if selected_bus else 0.0
    hotel_cost = float(selected_hotel.get("price_raw", 0)) if selected_hotel and selected_hotel.get("price_raw") else 0.0

    total_cost = bus_cost + hotel_cost
    budget_compliant = True
    if hotel_budget and hotel_cost > hotel_budget:
        budget_compliant = False

    # Deep links
    to_city = state.get("to_city", "")
    from_city = state.get("from_city", "")
    hotel_name = selected_hotel.get("name", "") if selected_hotel else ""

    deep_links = {
        "makemytrip_bus": f"https://www.makemytrip.com/bus-tickets/{from_city.lower()}-{to_city.lower()}-bus-ticket-booking.html",
        "booking_com_hotel": selected_hotel.get("links", {}).get("booking_com_direct", "") if selected_hotel else "",
        "google_maps_hotel": selected_hotel.get("links", {}).get("google_maps", "") if selected_hotel else ""
    }

    return {
        "total_cost": total_cost,
        "budget_compliant": budget_compliant,
        "deep_links": deep_links
    }
