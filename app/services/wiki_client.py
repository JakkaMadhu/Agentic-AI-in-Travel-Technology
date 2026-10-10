import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any

def fetch_city_attractions(city_name: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Fetch notable landmarks and sights for a city using Wikipedia API."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"tourist attractions in {city_name}",
        "gsrlimit": str(limit),
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
    req = urllib.request.Request(url, headers={"User-Agent": "AgenticTravelTech/1.0"})

    attractions = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})

            for page_id, item in pages.items():
                title = item.get("title", "")
                attractions.append({
                    "id": f"WIKI-{page_id}",
                    "title": title,
                    "summary": item.get("extract", "").strip(),
                    "photo_url": item.get("thumbnail", {}).get("source"),
                    "wikipedia_url": item.get("fullurl", f"https://en.wikipedia.org/?curid={page_id}"),
                    "google_maps_url": f"https://maps.google.com/?q={urllib.parse.quote(title + ' ' + city_name)}"
                })
    except Exception:
        pass

    return attractions
