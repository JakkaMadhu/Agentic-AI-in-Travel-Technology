"""
Test 1: Bus Search & Filter Engine
Project: AgenticTravelTech (TBS RoamAgent)
Description: Tests deterministic bus schedule matching, arrival deadline filters,
and operator deep links without external API dependency.
"""

import json
import os
from pathlib import Path
import env_loader

def load_buses():
    env_path = os.getenv("BUSES_DATA_PATH", "")
    if env_path:
        data_path = (Path(__file__).parent / env_path).resolve()
        if not data_path.exists():
            data_path = Path(__file__).parent.parent / "data" / "buses.json"
    else:
        data_path = Path(__file__).parent.parent / "data" / "buses.json"

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_buses(from_city, to_city, max_arrival_time=None, bus_type_preference=None):
    buses = load_buses()
    results = []

    for bus in buses:
        # Match cities (case-insensitive)
        if bus["from_city"].lower() != from_city.lower() or bus["to_city"].lower() != to_city.lower():
            continue

        # Filter by arrival deadline (e.g., "08:30")
        if max_arrival_time and bus["arrival_time"] > max_arrival_time:
            continue

        # Filter by bus type (e.g., "Sleeper")
        if bus_type_preference and bus_type_preference.lower() not in bus["bus_type"].lower():
            continue

        results.append(bus)

    # Sort by fare (lowest first) or departure time
    results.sort(key=lambda x: x["fare"]["total"])
    return results

if __name__ == "__main__":
    print("=" * 65)
    print("TEST 1: BUS SEARCH ENGINE")
    print("Origin: Visakhapatnam | Destination: Hyderabad")
    print("Constraint: AC Sleeper | Max Arrival: 08:30 AM")
    print("=" * 65)

    matches = search_buses(
        from_city="Visakhapatnam",
        to_city="Hyderabad",
        max_arrival_time="08:30",
        bus_type_preference="Sleeper"
    )

    print(f"\nFound {len(matches)} matching bus services:\n")

    for i, bus in enumerate(matches, 1):
        print(f"[{i}] {bus['operator']} - {bus['service_name']}")
        print(f"    Type: {bus['bus_type']} | Model: {bus['bus_model']}")
        print(f"    Timings: {bus['departure_time']} (Vizag) -> {bus['arrival_time']} (Hyd) | Duration: {bus['duration']}")
        print(f"    Fare: INR {bus['fare']['total']} (Base INR {bus['fare']['base']} + Tax INR {bus['fare']['tax']})")
        print(f"    Available Seats: {bus['seats']['available']} seats (Ladies: {bus['seats']['ladies_seats_available']})")
        print(f"    Boarding Stop 1: {bus['boarding_points'][0]['name']} at {bus['boarding_points'][0]['time']}")
        print(f"    GPS Boarding Link: {bus['boarding_points'][0]['map_link']}")
        print(f"    Official Booking URL: {bus['links']['official_booking_url']}")
        print(f"    RedBus Search URL: {bus['links']['aggregator_search_url']}")
        print("-" * 65)
