import math
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.state import TravelPlanState

def synthesizer_node(state: TravelPlanState) -> Dict[str, Any]:
    """Graph node: Synthesize budget, compute group totals, and formulate day-by-day itinerary."""
    selected_bus = state.get("selected_bus")
    selected_hotel = state.get("selected_hotel")
    passengers = max(1, int(state.get("passengers", 1)))
    duration_days = max(1, int(state.get("duration_days") or 2))

    transit_budget = float(state.get("transit_budget") or 0.0)
    hotel_budget = float(state.get("hotel_budget") or 0.0)
    allocated_budget = round(transit_budget + hotel_budget, 2)

    rooms = math.ceil(passengers / 2)
    nights = max(1, duration_days - 1) if duration_days > 1 else 1

    # Transit calculation
    price_per_seat = float(selected_bus.get("price_per_seat", 0.0)) if selected_bus else 0.0
    return_bus_required = state.get("return_bus_required")
    if return_bus_required is None:
        return_bus_required = True

    selected_return_bus = state.get("selected_return_bus") if return_bus_required else None
    return_price_per_seat = float(selected_return_bus.get("price_per_seat", 0.0)) if selected_return_bus else 0.0
    transit_total = round((price_per_seat + return_price_per_seat) * passengers, 2)

    # Hotel calculation
    price_per_night = float(selected_hotel.get("price_per_night", 0.0)) if selected_hotel else 0.0
    hotel_total = round(price_per_night * nights * rooms, 2)

    total_cost = round(transit_total + hotel_total, 2)
    budget_compliant = (total_cost <= allocated_budget) if allocated_budget > 0 else True
    savings = round(max(0.0, allocated_budget - total_cost), 2) if allocated_budget > 0 else 0.0

    # Build dynamic day-by-day itinerary
    attractions = state.get("tourist_attractions", [])
    travel_date_str = state.get("travel_date") or datetime.now().strftime("%Y-%m-%d")
    try:
        base_date = datetime.strptime(travel_date_str, "%Y-%m-%d")
    except Exception:
        base_date = datetime.now()

    to_c = state.get("to_city", "Destination")
    formatted_activities = []
    for idx, att in enumerate(attractions):
        formatted_activities.append({
            "name": att.get("name") or att.get("title", f"Landmark {idx + 1}"),
            "description": att.get("description") or att.get("summary", ""),
            "recommended_duration_hours": float(att.get("recommended_duration_hours", 2.0)),
            "photo_url": att.get("photo_url"),
            "google_maps_url": att.get("google_maps_url"),
            "wikipedia_url": att.get("wikipedia_url"),
            "latitude": float(att.get("latitude")) if att.get("latitude") is not None else None,
            "longitude": float(att.get("longitude")) if att.get("longitude") is not None else None
        })

    # Distribute attractions across days
    itinerary = []
    chunk_size = max(1, math.ceil(len(formatted_activities) / duration_days)) if formatted_activities else 2

    cur_idx = 0
    for day_num in range(1, duration_days + 1):
        day_date = (base_date + timedelta(days=day_num - 1)).strftime("%Y-%m-%d")
        day_acts = formatted_activities[cur_idx:cur_idx + chunk_size]
        cur_idx += chunk_size

        if not day_acts:
            themes = [
                (f"Explore {to_c} Town Center & Culture", f"Leisure stroll through historical regional commercial center and culinary spots in {to_c}."),
                (f"Scenic Viewpoints & Nature Trail in {to_c}", f"Visit popular panoramic vistas and nature lookouts around {to_c}."),
                (f"Local Artisanal Markets & Souvenirs", f"Experience regional craft centers, tea or spice shops, and souvenirs in {to_c}."),
                (f"Heritage Walk & Regional Flavors", f"Sample iconic local gastronomy and discover architectural landmarks in {to_c}.")
            ]
            from app.services.wiki_client import _get_city_coordinates_from_wiki
            center_coords = _get_city_coordinates_from_wiki(to_c) or (12.9716, 77.5946)
            c_lat, c_lon = center_coords
            theme_title, theme_desc = themes[(day_num - 1) % len(themes)]
            day_acts.append({
                "name": theme_title,
                "description": theme_desc,
                "recommended_duration_hours": 2.5,
                "photo_url": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=800&auto=format&fit=crop&q=80",
                "google_maps_url": f"https://maps.google.com/?q={to_c}+center",
                "wikipedia_url": f"https://en.wikipedia.org/wiki/{to_c}",
                "latitude": round(c_lat + (0.003 * day_num), 5),
                "longitude": round(c_lon + (0.003 * day_num), 5)
            })

        itinerary.append({
            "day": day_num,
            "date": day_date,
            "activities": day_acts
        })

    to_city = state.get("to_city", "")
    from_city = state.get("from_city", "")
    deep_links = {
        "makemytrip_bus": f"https://www.makemytrip.com/bus-tickets/{from_city.lower()}-{to_city.lower()}-bus-ticket-booking.html",
        "makemytrip_return_bus": f"https://www.makemytrip.com/bus-tickets/{to_city.lower()}-{from_city.lower()}-bus-ticket-booking.html" if return_bus_required else "",
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
