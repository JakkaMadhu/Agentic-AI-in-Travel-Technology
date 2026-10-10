from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- Phase 1: Intent Parsing & Budget Breakdown ---

class TripIntentRequest(BaseModel):
    query: str = Field(..., description="Natural language travel query submitted by user")
    client_session_uuid: Optional[str] = Field(None, description="Optional client-generated UUID")

class ExtractedParameters(BaseModel):
    from_city: str
    to_city: str
    travel_date: Optional[str] = None
    passengers: int = 1
    bus_type: Optional[str] = None
    arrival_deadline: Optional[str] = None
    total_budget: Optional[float] = None
    currency: str = "INR"

class CalculationBasis(BaseModel):
    transit_percentage: float = 30.0
    lodging_percentage: float = 40.0
    reserve_percentage: float = 30.0
    room_count: int = 1

class BudgetBreakdown(BaseModel):
    transit_cap: float
    lodging_cap: float
    daily_reserve: float
    calculation_basis: CalculationBasis

class TripIntentResponse(BaseModel):
    session_uuid: str
    status: str
    extracted_parameters: ExtractedParameters
    budget_breakdown: BudgetBreakdown
    created_at: datetime


# --- Phase 2: Verified Plan Execution ---

class TripPlanRequest(BaseModel):
    session_uuid: str = Field(..., description="UUID of session created in Phase 1")
    from_city: str
    to_city: str
    travel_date: str
    passengers: int = Field(default=1, ge=1)
    bus_type: Optional[str] = None
    arrival_deadline: Optional[str] = None
    transit_budget: float = Field(..., description="User-confirmed transit budget cap")
    hotel_budget: float = Field(..., description="User-confirmed hotel budget cap")
    currency: str = "INR"

class TransitOption(BaseModel):
    operator: str
    bus_type: str
    departure_time: str
    arrival_time: str
    price_per_seat: float
    total_price: float
    booking_reference_url: str

class TransitSection(BaseModel):
    selected: Optional[TransitOption] = None
    alternatives: List[TransitOption] = []

class AccommodationOption(BaseModel):
    hotel_name: str
    star_rating: Optional[float] = 0.0
    nights: int = 2
    rooms: int = 1
    price_per_night: float
    total_price: float
    booking_reference_url: str

class AccommodationSection(BaseModel):
    selected: Optional[AccommodationOption] = None
    alternatives: List[AccommodationOption] = []

class ActivityItem(BaseModel):
    name: str
    description: str
    recommended_duration_hours: float

class DayItinerary(BaseModel):
    day: int
    date: str
    activities: List[ActivityItem] = []

class PlanSummary(BaseModel):
    total_estimated_cost: float
    allocated_budget: float
    budget_compliant: bool
    savings: float
    currency: str = "INR"

class TripPlanResponse(BaseModel):
    session_uuid: str
    status: str
    summary: PlanSummary
    transit: TransitSection
    accommodation: AccommodationSection
    itinerary: List[DayItinerary] = []
    updated_at: datetime


# --- Session Retrieval & History ---

class TripDetailResponse(BaseModel):
    session_uuid: str
    user_query: str
    status: str
    parsed_intent: Optional[Dict[str, Any]] = None
    final_plan: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class TripHistoryItem(BaseModel):
    session_uuid: str
    from_city: Optional[str] = None
    to_city: Optional[str] = None
    travel_date: Optional[str] = None
    status: str
    total_cost: Optional[float] = None
    currency: str = "INR"
    created_at: datetime

class TripHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[TripHistoryItem]
