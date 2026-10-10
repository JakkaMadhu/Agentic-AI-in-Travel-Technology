import math
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.state import TravelPlanState

def synthesizer_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Synthesize budget, compute group totals, and formulate day-by-day itinerary."""
    selected_bus = state.get("selected_bus")
    selected_hotel = state.get("selected_hotel")
    passengers = max(1, int(state.get("passengers", 1)))

    transit_budget = float(state.get("transit_budget") or 0.0)
    hotel_budget = float(state.get("hotel_budget") or 0.0)
    allocated_budget = round(transit_budget + hotel_budget, 2)

    rooms = math.ceil(passengers / 2)
    nights = 2

    # Transit calculation
    price_per_seat = float(selected_bus.get("price_per_seat", 0.0)) if selected_bus else 0.0
    transit_total = round(price_per_seat * passengers, 2)

    # Hotel calculation
    price_per_night = float(selected_hotel.get("price_per_night", 0.0)) if selected_hotel else 0.0
    hotel_total = round(price_per_night * nights * rooms, 2)

    total_cost = round(transit_total + hotel_total, 2)
    budget_compliant = (total_cost <= allocated_budget) if allocated_budget > 0 else True
    savings = round(max(0.0, allocated_budget - total_cost), 2) if allocated_budget > 0 else 0.0

    # Build day-by-day itinerary
    attractions = state.get("tourist_attractions", [])
    travel_date_str = state.get("travel_date") or datetime.now().strftime("%Y-%m-%d")
    try:
        base_date = datetime.strptime(travel_date_str, "%Y-%m-%d")
    except Exception:
        base_date = datetime.now()

    day1_date = (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    day2_date = (base_date + timedelta(days=2)).strftime("%Y-%m-%d")

    day1_activities = []
    day2_activities = []

    for idx, att in enumerate(attractions):
        item = {
            "name": att.get("name") or att.get("title", f"Landmark {idx + 1}"),
            "description": att.get("description") or att.get("summary", ""),
            "recommended_duration_hours": float(att.get("recommended_duration_hours", 2.0))
        }
        if idx < 2:
            day1_activities.append(item)
        else:
            day2_activities.append(item)

    # Ensure Day 2 has at least 1 activity if Day 1 has some
    if day1_activities and not day2_activities:
        day2_activities.append({
            "name": f"Explore {state.get('to_city', 'City')} Town & Local Markets",
            "description": "Leisure stroll through historical regional commercial center and local markets.",
            "recommended_duration_hours": 2.5
        })

    itinerary = [
        {"day": 1, "date": day1_date, "activities": day1_activities},
        {"day": 2, "date": day2_date, "activities": day2_activities}
    ]

    to_city = state.get("to_city", "")
    from_city = state.get("from_city", "")
    deep_links = {
        "makemytrip_bus": f"https://www.makemytrip.com/bus-tickets/{from_city.lower()}-{to_city.lower()}-bus-ticket-booking.html",
        "booking_com_hotel": selected_hotel.get("booking_reference_url", "") if selected_hotel else ""
    }

    return {
        "total_cost": total_cost,
        "allocated_budget": allocated_budget,
        "budget_compliant": budget_compliant,
        "savings": savings,
        "itinerary": itinerary,
        "deep_links": deep_links
    }
