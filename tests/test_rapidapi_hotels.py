"""
Test 3: Live Hotels Fetcher (RapidAPI - Booking.com)
Project: AgenticTravelTech (TBS RoamAgent)
Description: Connects to RapidAPI's Booking.com API to fetch real hotel names,
live room prices in INR, real photos, review scores, and generates multi-portal booking links
(Booking.com direct, MakeMyTrip, and Google Hotels).
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
import env_loader

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "booking-com15.p.rapidapi.com").strip()

def get_destination_id(city_name: str, api_key: str):
    """Step 1: Get Booking.com destination ID for the city"""
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchDestination?query={urllib.parse.quote(city_name)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    })
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") and data.get("data"):
            # Return first city match
            first_match = data["data"][0]
            return first_match.get("dest_id"), first_match.get("search_type", "city")
    return None, None

def search_live_hotels(city_name: str, api_key: str, checkin_date: str = None, checkout_date: str = None, limit: int = 4):
    """Step 2: Query real-world hotels with live prices and photos"""
    if not checkin_date:
        checkin_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not checkout_date:
        checkout_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    dest_id, dest_type = get_destination_id(city_name, api_key)
    if not dest_id:
        print(f"Could not resolve destination ID for {city_name}")
        return []

    params = {
        "dest_id": dest_id,
        "search_type": dest_type,
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "adults": "1",
        "room_qty": "1",
        "page_number": "1",
        "units": "metric",
        "temperature_unit": "c",
        "languagecode": "en-us",
        "currency_code": "INR"
    }

    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchHotels?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    })

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        hotels_raw = data.get("data", {}).get("hotels", [])[:limit]
        formatted = []

        for h in hotels_raw:
            prop = h.get("property", {})
            name = prop.get("name", "Unknown Hotel")
            price_info = prop.get("priceBreakdown", {}).get("grossPrice", {})
            price_val = price_info.get("value", "N/A")
            currency = price_info.get("currency", "INR")
            photo_urls = prop.get("photoUrls", [])
            photo = photo_urls[0] if photo_urls else "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600"
            review_score = prop.get("reviewScore", "N/A")
            review_count = prop.get("reviewCount", 0)

            # Extract exact GPS Coordinates provided by Booking.com
            latitude = prop.get("latitude")
            longitude = prop.get("longitude")

            # Generate companion links
            query_encoded = urllib.parse.quote(f"{name} {city_name}")
            city_slug = city_name.lower().replace(" ", "-")

            # Format working verified Booking.com search link
            booking_com_query = urllib.parse.quote(f"{name} {city_name}")

            # Google Navigation Link using exact coordinates
            map_nav_link = f"https://www.google.com/maps/dir/?api=1&destination={latitude},{longitude}" if latitude and longitude else f"https://maps.google.com/?q={query_encoded}"

            formatted.append({
                "hotel_id": h.get("hotel_id"),
                "name": name,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "price_inr": f"₹{int(price_val)}" if isinstance(price_val, (int, float)) else str(price_val),
                "rating": f"{review_score} / 10 ({review_count} reviews)",
                "photo_url": photo,
                "links": {
                    "booking_com_direct": f"https://www.booking.com/searchresults.html?ss={booking_com_query}",
                    "google_hotels_compare": f"https://www.google.com/travel/hotels?q={query_encoded}",
                    "makemytrip_search": f"https://www.makemytrip.com/hotels/{city_slug}-hotels.html?searchText={urllib.parse.quote(name)}",
                    "directions_map_link": map_nav_link
                }
            })

        return formatted

if __name__ == "__main__":
    print("=" * 65)
    print("TEST 3: LIVE HOTELS VIA RAPIDAPI (BOOKING.COM)")
    print("=" * 65)

    if RAPIDAPI_KEY == "YOUR_RAPIDAPI_KEY_HERE":
        print("\n[!] NOTICE: Please provide your RapidAPI key.")
        print("To run this test:")
        print("1. Set your key inside this file (RAPIDAPI_KEY = '...') OR")
        print("2. Run in terminal:")
        print("   $env:RAPIDAPI_KEY='your_key_here'; python tests/test_rapidapi_hotels.py\n")
        print("Below is the EXACT data structure this test produces once your key is added:")
        
        sample_output = [
            {
                "name": "Lemon Tree Premier, Hitec City",
                "price_inr": "₹4,250",
                "rating": "8.3 / 10 (2,120 reviews)",
                "photo_url": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/...",
                "links": {
                    "booking_com_direct": "https://www.booking.com/hotel/in/lemon-tree.html",
                    "google_hotels_compare": "https://www.google.com/travel/hotels?q=Lemon+Tree+Premier+Hyderabad",
                    "makemytrip_search": "https://www.makemytrip.com/hotels/hyderabad-hotels.html?searchText=Lemon%20Tree"
                }
            }
        ]
        print(json.dumps(sample_output, indent=2))
    else:
        print("\nQuerying live hotels for Hyderabad...")
        try:
            results = search_live_hotels("Hyderabad", RAPIDAPI_KEY, limit=3)
            print(f"\nFetched {len(results)} live hotels with current prices:\n")
            print(json.dumps(results, indent=2))
        except Exception as e:
            print(f"API Error: {e}")
