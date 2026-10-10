import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.config import settings

def get_destination_id(city_name: str) -> Optional[str]:
    """Retrieve Booking.com destination ID for given city."""
    url = f"https://{settings.RAPIDAPI_HOST}/api/v1/hotels/searchDestination?query={urllib.parse.quote(city_name)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_HOST
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            if items:
                return items[0].get("dest_id")
    except Exception:
        pass
    return None

def fetch_live_hotels(city_name: str, max_budget: Optional[float] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch real-time hotel options with coordinates, price, and booking links."""
    dest_id = get_destination_id(city_name)
    if not dest_id:
        return []

    checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    checkout = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    params = {
        "dest_id": dest_id,
        "search_type": "CITY",
        "arrival_date": checkin,
        "departure_date": checkout,
        "adults": "1",
        "room_qty": "1",
        "currency_code": "INR",
        "order_by": "popularity"
    }

    url = f"https://{settings.RAPIDAPI_HOST}/api/v1/hotels/searchHotels?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_HOST
    })

    hotels = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_hotels = data.get("data", {}).get("hotels", [])

            for h in raw_hotels:
                property_data = h.get("property", {})
                price_breakdown = property_data.get("priceBreakdown", {}).get("grossPrice", {})
                price_val = price_breakdown.get("value")

                if max_budget and price_val and float(price_val) > max_budget:
                    continue

                lat = property_data.get("latitude")
                lon = property_data.get("longitude")
                name = property_data.get("name", "Unknown Hotel")

                hotels.append({
                    "hotel_id": property_data.get("id"),
                    "name": name,
                    "price_inr": f"₹{int(price_val)}" if price_val else "N/A",
                    "price_raw": price_val,
                    "latitude": lat,
                    "longitude": lon,
                    "rating": property_data.get("reviewScore"),
                    "photo_url": property_data.get("photoUrls", [None])[0],
                    "links": {
                        "booking_com_direct": f"https://www.booking.com/searchresults.html?ss={urllib.parse.quote(name + ' ' + city_name)}",
                        "google_maps": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else f"https://maps.google.com/?q={urllib.parse.quote(name)}"
                    }
                })

                if len(hotels) >= limit:
                    break
    except Exception:
        pass

    return hotels
