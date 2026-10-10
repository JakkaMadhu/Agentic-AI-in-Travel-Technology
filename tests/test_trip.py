"""
Integration tests for Trip Planning API (Phase 1, Phase 2, History, Session Detail)
Project: AgenticTravelTech
"""

import os
import sys
from pathlib import Path
from peewee import SqliteDatabase
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

TEST_DB_FILE = "test_trip_temp.db"
test_db = SqliteDatabase(TEST_DB_FILE)

from app.models.base import BaseModel
from app.models.user import User
from app.models.travel import TripSession
from app.models.system import ApiLog

# Rebind all models to test_db
User._meta.database = test_db
TripSession._meta.database = test_db
ApiLog._meta.database = test_db
BaseModel._meta.database = test_db

from app.main import app
from app.dependencies import get_db

def override_get_db():
    if test_db.is_closed():
        test_db.connect(reuse_if_open=True)
    try:
        yield test_db
    finally:
        pass

def setup_module():
    """Initialize test database tables and dependency overrides."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass
    test_db.connect(reuse_if_open=True)
    test_db.create_tables([User, TripSession, ApiLog], safe=True)
    app.dependency_overrides[get_db] = override_get_db

def teardown_module():
    """Clean up test database and reset overrides."""
    app.dependency_overrides.clear()
    if not test_db.is_closed():
        test_db.close()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

def test_full_trip_lifecycle():
    client = TestClient(app)

    # 1. Register and authenticate user
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "traveler@example.com",
        "password": "mypassword123"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "email": "traveler@example.com",
        "password": "mypassword123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Phase 1: Parse Trip Intent
    intent_payload = {
        "query": "Plan a budget weekend trip from Bangalore to Ooty for 2 people under 15000 INR starting next Friday, AC sleeper bus preferred, reach before 8 AM"
    }
    intent_res = client.post("/api/v1/trip/intent", json=intent_payload, headers=auth_headers)
    assert intent_res.status_code == 201, intent_res.text
    intent_data = intent_res.json()

    assert "session_uuid" in intent_data
    session_uuid = intent_data["session_uuid"]
    assert intent_data["status"] == "INTENT_PARSED"

    params = intent_data["extracted_parameters"]
    assert params["from_city"].lower() in ("bangalore", "bengaluru")
    assert params["to_city"].lower() == "ooty"
    assert params["passengers"] == 2
    assert params["total_budget"] == 15000.0

    breakdown = intent_data["budget_breakdown"]
    assert breakdown["transit_cap"] == 4500.0  # 30% of 15000
    assert breakdown["lodging_cap"] == 6000.0  # 40% of 15000
    assert breakdown["daily_reserve"] == 4500.0  # 30% of 15000
    assert breakdown["calculation_basis"]["room_count"] == 1

    # Verify session persisted in DB
    session_record = TripSession.get_or_none(TripSession.session_uuid == session_uuid)
    assert session_record is not None
    assert session_record.status == "INTENT_PARSED"

    # Verify ApiLog entry
    logs = list(ApiLog.select().where(ApiLog.session == session_record))
    assert len(logs) >= 1
    assert logs[0].service_name == "groq_intent_parser"

    # 3. Phase 2: Execute Plan Generation
    plan_payload = {
        "session_uuid": session_uuid,
        "from_city": "Bangalore",
        "to_city": "Ooty",
        "travel_date": params["travel_date"],
        "passengers": 2,
        "bus_type": "AC Sleeper",
        "arrival_deadline": "08:00",
        "transit_budget": breakdown["transit_cap"],
        "hotel_budget": breakdown["lodging_cap"],
        "currency": "INR"
    }

    plan_res = client.post("/api/v1/trip/plan", json=plan_payload, headers=auth_headers)
    assert plan_res.status_code == 200, plan_res.text
    plan_data = plan_res.json()

    assert plan_data["session_uuid"] == session_uuid
    assert plan_data["status"] == "PLAN_GENERATED"

    # Verify Summary
    summary = plan_data["summary"]
    assert summary["total_estimated_cost"] > 0
    assert summary["allocated_budget"] == 10500.0
    assert "budget_compliant" in summary

    # Verify Transit
    transit = plan_data["transit"]
    assert transit["selected"] is not None
    assert transit["selected"]["price_per_seat"] > 0
    assert transit["selected"]["total_price"] == transit["selected"]["price_per_seat"] * 2
    assert "booking_reference_url" in transit["selected"]

    # Verify Accommodation
    acc = plan_data["accommodation"]
    assert acc["selected"] is not None
    assert acc["selected"]["price_per_night"] > 0
    assert acc["selected"]["total_price"] > 0
    assert "booking_reference_url" in acc["selected"]

    # Verify Itinerary
    itinerary = plan_data["itinerary"]
    assert len(itinerary) >= 2
    assert itinerary[0]["day"] == 1
    assert len(itinerary[0]["activities"]) >= 1

    # Verify updated session status in DB
    session_record_updated = TripSession.get_or_none(TripSession.session_uuid == session_uuid)
    assert session_record_updated.status == "PLAN_GENERATED"
    assert session_record_updated.final_plan is not None

    # 4. Conflict check: calling plan generation again returns 409
    dup_plan_res = client.post("/api/v1/trip/plan", json=plan_payload, headers=auth_headers)
    assert dup_plan_res.status_code == 409

    # 5. Retrieve Session Details
    detail_res = client.get(f"/api/v1/trip/{session_uuid}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["session_uuid"] == session_uuid
    assert detail_data["status"] == "PLAN_GENERATED"
    assert detail_data["parsed_intent"] is not None
    assert detail_data["final_plan"] is not None

    # 6. Retrieve User History
    history_res = client.get("/api/v1/trip/history?limit=10&offset=0", headers=auth_headers)
    assert history_res.status_code == 200
    hist_data = history_res.json()
    assert hist_data["total"] >= 1
    assert len(hist_data["items"]) >= 1
    assert hist_data["items"][0]["session_uuid"] == session_uuid

    # 7. Nonexistent session returns 404
    missing_res = client.get("/api/v1/trip/nonexistent-uuid-12345", headers=auth_headers)
    assert missing_res.status_code == 404

if __name__ == "__main__":
    setup_module()
    try:
        test_full_trip_lifecycle()
        print("PASS: test_full_trip_lifecycle")
        print("\nALL TRIP PLANNING API TESTS PASSED.")
    finally:
        teardown_module()
