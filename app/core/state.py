from typing import TypedDict, Optional, List, Dict, Any

class TravelPlanState(TypedDict):
    session_id: str
    from_city: str
    to_city: str
    travel_date: Optional[str]
    bus_type: Optional[str]
    arrival_deadline: Optional[str]
    hotel_budget: Optional[float]
    currency: str

    # Candidate and selected items
    bus_candidates: List[Dict[str, Any]]
    selected_bus: Optional[Dict[str, Any]]
    
    hotel_candidates: List[Dict[str, Any]]
    selected_hotel: Optional[Dict[str, Any]]
    
    tourist_attractions: List[Dict[str, Any]]
    
    # Financial and completion metrics
    total_cost: float
    budget_compliant: bool
    deep_links: Dict[str, str]
    errors: List[str]
