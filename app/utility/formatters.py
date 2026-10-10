import re
from typing import Optional

def normalize_price_inr(price_str: Optional[str]) -> Optional[float]:
    """Extract numeric price from strings like '₹3,600' or 'INR 2500'."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(price_str))
    try:
        return float(cleaned)
    except ValueError:
        return None

def format_currency_inr(amount: float) -> str:
    """Format float into canonical INR string."""
    return f"₹{amount:,.2f}"
