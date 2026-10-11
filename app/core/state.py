from typing import TypedDict, Optional, List, Dict, Any

class TravelPlanState(TypedDict):
    session_id: str
    from_city: str
    to_city: str
    travel_date: Optional[str]
    duration_days: Optional[int]
    passengers: int
    bus_type: Optional[str]
    arrival_deadline: Optional[str]
    transit_budget: Optional[float]
    hotel_budget: Optional[float]
    currency: str
    return_bus_required: Optional[bool]

    # Candidates and selections
    bus_candidates: List[Dict[str, Any]]
    selected_bus: Optional[Dict[str, Any]]
    alternative_buses: List[Dict[str, Any]]

    return_bus_candidates: List[Dict[str, Any]]
    selected_return_bus: Optional[Dict[str, Any]]
    alternative_return_buses: List[Dict[str, Any]]

    hotel_candidates: List[Dict[str, Any]]
    selected_hotel: Optional[Dict[str, Any]]
    alternative_hotels: List[Dict[str, Any]]

    tourist_attractions: List[Dict[str, Any]]
    itinerary: List[Dict[str, Any]]

    # Financial and completion metrics
    total_cost: float
    allocated_budget: float
    budget_compliant: bool
    savings: float
    deep_links: Dict[str, str]
    errors: List[str]
