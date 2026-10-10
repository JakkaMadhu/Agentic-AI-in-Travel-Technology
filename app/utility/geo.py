import math
from typing import Tuple, Optional

def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance in kilometers between two GPS coordinates (lat, lon)."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return r * c

def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> bool:
    """Validate latitude and longitude ranges."""
    if lat is None or lon is None:
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
