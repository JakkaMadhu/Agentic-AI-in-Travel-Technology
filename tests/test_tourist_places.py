"""
Test 2: Tourist Places Fetcher (Wikipedia API)
Project: AgenticTravelTech (TBS RoamAgent)
Description: 100% Free, No Key needed. Fetches verified landmarks, summaries,
real thumbnail photos, and Google Map links for any destination city.
"""

import json
import urllib.parse
import urllib.request

def fetch_attractions(city_name: str, limit: int = 4):
    query = f"{city_name} tourist attractions landmarks"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": limit,
        "prop": "extracts|pageimages|info",
        "exintro": "1",
        "explaintext": "1",
        "exchars": "200",
        "piprop": "thumbnail",
        "pithumbsize": "600",
        "inprop": "url",
        "format": "json",
        "origin": "*"
    }

    url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "TBS-RoamAgent/1.0 (Hackathon)"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            attractions = []

            for page_id, item in pages.items():
                title = item.get("title", "")
                attractions.append({
                    "id": f"WIKI-{page_id}",
                    "title": title,
                    "summary": item.get("extract", "").strip(),
                    "photo_url": item.get("thumbnail", {}).get("source", "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=600"),
                    "wikipedia_url": item.get("fullurl", f"https://en.wikipedia.org/?curid={page_id}"),
                    "google_maps_url": f"https://maps.google.com/?q={urllib.parse.quote(title + ' ' + city_name)}"
                })
            return attractions
    except Exception as e:
        print(f"Error fetching attractions: {e}")
        return []

if __name__ == "__main__":
    city = "Hyderabad"
    print("=" * 65)
    print(f"TEST 2: TOURIST PLACES FETCHER FOR: {city.upper()}")
    print("=" * 65)

    places = fetch_attractions(city, limit=3)
    print(f"\nFetched {len(places)} verified attractions:\n")

    for i, place in enumerate(places, 1):
        print(f"[{i}] {place['title']}")
        print(f"    Summary: {place['summary'][:120]}...")
        print(f"    Photo URL: {place['photo_url']}")
        print(f"    Map Link: {place['google_maps_url']}")
        print(f"    Wiki Article: {place['wikipedia_url']}")
        print("-" * 65)
