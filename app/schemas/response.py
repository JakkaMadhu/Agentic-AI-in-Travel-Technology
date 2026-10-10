from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IntentParseResponse(BaseModel):
    session_id: str
    from_city: Optional[str]
    to_city: Optional[str]
    travel_date: Optional[str]
    bus_type: Optional[str]
    arrival_deadline: Optional[str]
    hotel_budget: Optional[float]
    currency: str = "INR"

class PlanGenerationResponse(BaseModel):
    session_id: str
    from_city: str
    to_city: str
    travel_date: Optional[str]
    total_cost: float
    budget_compliant: bool
    selected_bus: Optional[Dict[str, Any]]
    alternative_buses: List[Dict[str, Any]] = []
    selected_hotel: Optional[Dict[str, Any]]
    alternative_hotels: List[Dict[str, Any]] = []
    tourist_attractions: List[Dict[str, Any]] = []
    deep_links: Dict[str, str] = {}
