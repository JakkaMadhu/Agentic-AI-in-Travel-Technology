from typing import Optional
from pydantic import BaseModel, Field

class IntentParseRequest(BaseModel):
    query: str = Field(..., description="Natural language travel query submitted by user")
    session_id: Optional[str] = Field(None, description="Optional client session identifier")

class PlanGenerationRequest(BaseModel):
    session_id: str = Field(..., description="Active session identifier")
    from_city: str = Field(..., description="Origin city name")
    to_city: str = Field(..., description="Destination city name")
    travel_date: Optional[str] = Field(None, description="Date of travel (YYYY-MM-DD or descriptor)")
    bus_type: Optional[str] = Field(None, description="Preferred seating tier, e.g. AC Sleeper")
    arrival_deadline: Optional[str] = Field(None, description="Target arrival time constraint in 24hr format (HH:MM)")
    hotel_budget: Optional[float] = Field(None, description="Maximum budget limit for lodging in INR")
    currency: str = Field("INR", description="Currency standard")
