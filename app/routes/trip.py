import math
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.travel import TripSession
from app.models.system import ApiLog
from app.services.groq_client import extract_intent_with_groq
from app.core.graph import build_travel_graph
from app.core.state import TravelPlanState
from app.schemas.trip import (
    TripIntentRequest,
    ExtractedParameters,
    CalculationBasis,
    BudgetBreakdown,
    TripIntentResponse,
    TripPlanRequest,
    TransitOption,
    TransitSection,
    AccommodationOption,
    AccommodationSection,
    ActivityItem,
    DayItinerary,
    PlanSummary,
    TripPlanResponse,
    TripDetailResponse,
    TripHistoryItem,
    TripHistoryResponse,
    ClearHistoryResponse,
    DeleteTripResponse,
)

router = APIRouter(prefix="/api/v1/trip", tags=["Trip Planning"])

# Compile LangGraph workflow instance
travel_graph = build_travel_graph()

@router.post(
    "/intent",
    response_model=TripIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Parse natural language trip intent and calculate budget caps (Phase 1)"
)
def parse_trip_intent(
    request: TripIntentRequest,
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Extract travel constraints from prompt, calculate budget breakdown caps, and initialize session."""
    start_time = time.time()
    extracted = extract_intent_with_groq(request.query)
    latency_ms = int((time.time() - start_time) * 1000)

    from_city = extracted.get("from_city")
    to_city = extracted.get("to_city")

    if not from_city and to_city:
        from_city = "Bangalore" if to_city.lower() != "bangalore" else "Hyderabad"
    elif not to_city and from_city:
        to_city = "Ooty" if from_city.lower() != "ooty" else "Goa"

    if not from_city or not to_city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to extract destination from query. Please specify where you want to travel."
        )

    passengers = max(1, int(extracted.get("passengers", 1)))
    duration_days_raw = extracted.get("duration_days")
    duration_days = int(duration_days_raw) if duration_days_raw and int(duration_days_raw) >= 1 else None
    total_budget = float(extracted.get("total_budget") or (10000.0 * passengers))
    currency = extracted.get("currency", "INR")

    # Budget Breakdown Calculation
    transit_cap = round(total_budget * 0.30, 2)
    lodging_cap = round(total_budget * 0.40, 2)
    daily_reserve = round(total_budget * 0.30, 2)
    room_count = math.ceil(passengers / 2)
    nights = max(1, duration_days - 1) if duration_days and duration_days > 1 else (1 if duration_days else None)

    return_bus = extracted.get("return_bus")

    extracted_params = ExtractedParameters(
        from_city=from_city,
        to_city=to_city,
        travel_date=extracted.get("travel_date"),
        duration_days=duration_days,
        return_bus=return_bus,
        passengers=passengers,
        bus_type=extracted.get("bus_type", "AC Sleeper"),
        arrival_deadline=extracted.get("arrival_deadline"),
        total_budget=total_budget,
        currency=currency
    )

    budget_breakdown = BudgetBreakdown(
        transit_cap=transit_cap,
        lodging_cap=lodging_cap,
        daily_reserve=daily_reserve,
        calculation_basis=CalculationBasis(
            transit_percentage=30.0,
            lodging_percentage=40.0,
            reserve_percentage=30.0,
            room_count=room_count,
            duration_days=duration_days,
            nights=nights,
            return_bus=return_bus
        )
    )

    session_uuid = request.client_session_uuid or str(uuid.uuid4())

    # Persist session to PostgreSQL
    parsed_payload = {
        "extracted_parameters": extracted_params.model_dump(),
        "budget_breakdown": budget_breakdown.model_dump()
    }

    session = TripSession.create(
        user=current_user,
        session_uuid=session_uuid,
        user_query=request.query,
        status="INTENT_PARSED",
        parsed_intent=parsed_payload,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Audit log
    ApiLog.create(
        session=session,
        service_name="groq_intent_parser",
        endpoint="/api/v1/trip/intent",
        request_payload={"query": request.query},
        response_payload=parsed_payload,
        status_code=201,
        latency_ms=latency_ms,
        created_at=datetime.utcnow()
    )

    return TripIntentResponse(
        session_uuid=session.session_uuid,
        status="INTENT_PARSED",
        extracted_parameters=extracted_params,
        budget_breakdown=budget_breakdown,
        created_at=session.created_at
    )

@router.post(
    "/plan",
    response_model=TripPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-agent travel plan generation with confirmed constraints (Phase 2)"
)
def generate_trip_plan(
    request: TripPlanRequest,
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Execute LangGraph search pipeline with user-confirmed constraints and generate finalized itinerary."""
    session = TripSession.get_or_none(
        (TripSession.session_uuid == request.session_uuid) &
        (TripSession.user == current_user)
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if session.status == "PLAN_GENERATED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session already finalized or in invalid state: PLAN_GENERATED."
        )

    # Lock state to USER_CONFIRMED
    session.status = "USER_CONFIRMED"
    session.updated_at = datetime.utcnow()
    session.save()

    duration_days = max(1, int(getattr(request, "duration_days", None) or 2))
    if duration_days == 2 and session.parsed_intent:
        extracted = session.parsed_intent.get("extracted_parameters", {})
        if extracted.get("duration_days"):
            duration_days = max(1, int(extracted.get("duration_days")))

    # Execute LangGraph Pipeline
    initial_state: TravelPlanState = {
        "session_id": request.session_uuid,
        "from_city": request.from_city,
        "to_city": request.to_city,
        "travel_date": request.travel_date,
        "duration_days": duration_days,
        "return_bus_required": request.return_bus,
        "passengers": request.passengers,
        "bus_type": request.bus_type,
        "arrival_deadline": request.arrival_deadline,
        "transit_budget": request.transit_budget,
        "hotel_budget": request.hotel_budget,
        "currency": request.currency,
        "bus_candidates": [],
        "selected_bus": None,
        "alternative_buses": [],
        "return_bus_candidates": [],
        "selected_return_bus": None,
        "alternative_return_buses": [],
        "hotel_candidates": [],
        "selected_hotel": None,
        "alternative_hotels": [],
        "tourist_attractions": [],
        "itinerary": [],
        "total_cost": 0.0,
        "allocated_budget": request.transit_budget + request.hotel_budget,
        "budget_compliant": True,
        "savings": 0.0,
        "deep_links": {},
        "errors": []
    }

    start_time = time.time()
    try:
        final_state = travel_graph.invoke(initial_state)
    except Exception as e:
        session.status = "FAILED"
        session.updated_at = datetime.utcnow()
        session.save()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agentic graph execution failure: {str(e)}"
        )
    latency_ms = int((time.time() - start_time) * 1000)

    # Format transit response
    passengers = max(1, request.passengers)
    selected_bus_raw = final_state.get("selected_bus")
    selected_bus = None
    if selected_bus_raw:
        seat_price = float(selected_bus_raw.get("price_per_seat", 0.0))
        selected_bus = TransitOption(
            operator=selected_bus_raw.get("operator", "State Express"),
            bus_type=selected_bus_raw.get("bus_type", "AC Sleeper"),
            departure_time=selected_bus_raw.get("departure_time", "22:30"),
            arrival_time=selected_bus_raw.get("arrival_time", "06:15"),
            price_per_seat=seat_price,
            total_price=round(seat_price * passengers, 2),
            booking_reference_url=selected_bus_raw.get("booking_reference_url", ""),
            distance_km=float(selected_bus_raw["distance_km"]) if selected_bus_raw.get("distance_km") is not None else None,
            origin_coords=selected_bus_raw.get("origin_coords"),
            destination_coords=selected_bus_raw.get("destination_coords")
        )

    alt_buses = []
    for b in final_state.get("alternative_buses", []):
        seat_price = float(b.get("price_per_seat", 0.0))
        alt_buses.append(TransitOption(
            operator=b.get("operator", "Regional Travels"),
            bus_type=b.get("bus_type", "AC Sleeper"),
            departure_time=b.get("departure_time", "22:00"),
            arrival_time=b.get("arrival_time", "07:00"),
            price_per_seat=seat_price,
            total_price=round(seat_price * passengers, 2),
            booking_reference_url=b.get("booking_reference_url", ""),
            distance_km=float(b["distance_km"]) if b.get("distance_km") is not None else None,
            origin_coords=b.get("origin_coords"),
            destination_coords=b.get("destination_coords")
        ))

    # Format return bus response
    selected_return_bus_raw = final_state.get("selected_return_bus") if request.return_bus else None
    selected_return_bus = None
    if selected_return_bus_raw:
        ret_seat_price = float(selected_return_bus_raw.get("price_per_seat", 0.0))
        selected_return_bus = TransitOption(
            operator=selected_return_bus_raw.get("operator", "State Express Return"),
            bus_type=selected_return_bus_raw.get("bus_type", "AC Sleeper"),
            departure_time=selected_return_bus_raw.get("departure_time", "20:00"),
            arrival_time=selected_return_bus_raw.get("arrival_time", "05:00"),
            price_per_seat=ret_seat_price,
            total_price=round(ret_seat_price * passengers, 2),
            booking_reference_url=selected_return_bus_raw.get("booking_reference_url", ""),
            distance_km=float(selected_return_bus_raw["distance_km"]) if selected_return_bus_raw.get("distance_km") is not None else None,
            origin_coords=selected_return_bus_raw.get("origin_coords"),
            destination_coords=selected_return_bus_raw.get("destination_coords")
        )

    alt_return_buses = []
    if request.return_bus:
        for b in final_state.get("alternative_return_buses", []):
            ret_seat_price = float(b.get("price_per_seat", 0.0))
            alt_return_buses.append(TransitOption(
                operator=b.get("operator", "Regional Travels Return"),
                bus_type=b.get("bus_type", "AC Sleeper"),
                departure_time=b.get("departure_time", "21:30"),
                arrival_time=b.get("arrival_time", "06:30"),
                price_per_seat=ret_seat_price,
                total_price=round(ret_seat_price * passengers, 2),
                booking_reference_url=b.get("booking_reference_url", ""),
                distance_km=float(b["distance_km"]) if b.get("distance_km") is not None else None,
                origin_coords=b.get("origin_coords"),
                destination_coords=b.get("destination_coords")
            ))

    # Format accommodation response
    rooms = math.ceil(passengers / 2)
    nights = max(1, duration_days - 1) if duration_days > 1 else 1
    selected_hotel_raw = final_state.get("selected_hotel")
    selected_hotel = None
    if selected_hotel_raw:
        night_price = float(selected_hotel_raw.get("price_per_night", 2500.0))
        selected_hotel = AccommodationOption(
            hotel_name=selected_hotel_raw.get("hotel_name") or selected_hotel_raw.get("name", "Boutique Hotel"),
            star_rating=float(selected_hotel_raw.get("star_rating", 4.0)),
            nights=nights,
            rooms=rooms,
            price_per_night=night_price,
            total_price=round(night_price * nights * rooms, 2),
            booking_reference_url=selected_hotel_raw.get("booking_reference_url", ""),
            photo_url=selected_hotel_raw.get("photo_url")
        )

    alt_hotels = []
    for h in final_state.get("alternative_hotels", []):
        night_price = float(h.get("price_per_night", 2200.0))
        alt_hotels.append(AccommodationOption(
            hotel_name=h.get("hotel_name") or h.get("name", "Alternative Hotel"),
            star_rating=float(h.get("star_rating", 3.5)),
            nights=nights,
            rooms=rooms,
            price_per_night=night_price,
            total_price=round(night_price * nights * rooms, 2),
            booking_reference_url=h.get("booking_reference_url", ""),
            photo_url=h.get("photo_url")
        ))

    # Format itinerary response
    itinerary_items = []
    for day_data in final_state.get("itinerary", []):
        acts = [
            ActivityItem(
                name=a.get("name", ""),
                description=a.get("description", ""),
                recommended_duration_hours=float(a.get("recommended_duration_hours", 2.0)),
                photo_url=a.get("photo_url"),
                google_maps_url=a.get("google_maps_url"),
                wikipedia_url=a.get("wikipedia_url"),
                latitude=float(a["latitude"]) if a.get("latitude") is not None else None,
                longitude=float(a["longitude"]) if a.get("longitude") is not None else None
            )
            for a in day_data.get("activities", [])
        ]
        itinerary_items.append(DayItinerary(
            day=day_data.get("day", 1),
            date=day_data.get("date", ""),
            activities=acts
        ))

    summary = PlanSummary(
        total_estimated_cost=final_state.get("total_cost", 0.0),
        allocated_budget=final_state.get("allocated_budget", 0.0),
        budget_compliant=final_state.get("budget_compliant", True),
        savings=final_state.get("savings", 0.0),
        currency=request.currency
    )

    transit_section = TransitSection(
        selected=selected_bus,
        alternatives=alt_buses,
        return_selected=selected_return_bus,
        return_alternatives=alt_return_buses
    )
    accommodation_section = AccommodationSection(selected=selected_hotel, alternatives=alt_hotels)

    response_data = TripPlanResponse(
        session_uuid=session.session_uuid,
        status="PLAN_GENERATED",
        from_city=request.from_city,
        to_city=request.to_city,
        summary=summary,
        transit=transit_section,
        accommodation=accommodation_section,
        itinerary=itinerary_items,
        updated_at=datetime.utcnow()
    )

    # Persist finalized plan
    session.status = "PLAN_GENERATED"
    session.final_plan = response_data.model_dump(mode="json")
    session.updated_at = datetime.utcnow()
    session.save()

    # Audit log
    ApiLog.create(
        session=session,
        service_name="langgraph_planner",
        endpoint="/api/v1/trip/plan",
        request_payload=request.model_dump(),
        response_payload=response_data.model_dump(mode="json"),
        status_code=200,
        latency_ms=latency_ms,
        created_at=datetime.utcnow()
    )

    return response_data

@router.get(
    "/history",
    response_model=TripHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve user trip history with pagination"
)
def get_user_trip_history(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Fetch paginated trip sessions belonging to the authenticated user."""
    query = TripSession.select().where(TripSession.user == current_user).order_by(TripSession.created_at.desc())
    total = query.count()
    sessions = query.offset(offset).limit(limit)

    items = []
    for s in sessions:
        parsed = s.parsed_intent or {}
        extracted = parsed.get("extracted_parameters", {})
        final = s.final_plan or {}
        summary = final.get("summary", {})

        items.append(TripHistoryItem(
            session_uuid=s.session_uuid,
            from_city=extracted.get("from_city"),
            to_city=extracted.get("to_city"),
            travel_date=extracted.get("travel_date"),
            status=s.status,
            total_cost=summary.get("total_estimated_cost"),
            currency=summary.get("currency", "INR"),
            created_at=s.created_at
        ))

    return TripHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items
    )

@router.delete(
    "/history",
    response_model=ClearHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear all trip history for the authenticated user"
)
def clear_user_trip_history(
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Delete all trip sessions belonging to the authenticated user."""
    delete_query = TripSession.delete().where(TripSession.user == current_user)
    deleted_count = delete_query.execute()

    return ClearHistoryResponse(
        deleted_count=deleted_count,
        message=f"Successfully cleared {deleted_count} trip history record(s)."
    )

@router.get(
    "/{session_uuid}",
    response_model=TripDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve trip session details by UUID"
)
def get_trip_session(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Fetch real-time state and full payload of an existing trip session."""
    session = TripSession.get_or_none(
        (TripSession.session_uuid == session_uuid) &
        (TripSession.user == current_user)
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session with specified UUID does not exist."
        )

    return TripDetailResponse(
        session_uuid=session.session_uuid,
        user_query=session.user_query,
        status=session.status,
        parsed_intent=session.parsed_intent,
        final_plan=session.final_plan,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@router.delete(
    "/{session_uuid}",
    response_model=DeleteTripResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a specific trip session by UUID"
)
def delete_trip_session(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    _db=Depends(get_db)
):
    """Delete a single trip session belonging to the authenticated user."""
    delete_query = TripSession.delete().where(
        (TripSession.session_uuid == session_uuid) &
        (TripSession.user == current_user)
    )
    deleted_count = delete_query.execute()

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip session with specified UUID not found or not owned by user."
        )

    return DeleteTripResponse(
        session_uuid=session_uuid,
        message="Trip session deleted successfully."
    )
