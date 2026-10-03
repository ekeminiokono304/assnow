from .config import (FREQUENCIES, PRICING, PROPERTY_SIZES, RANGE_HIGH, RANGE_LOW,
                     RECURRING_DISCOUNT, ROUND_TO, SERVICES)


def _round(n: float) -> int:
    return int(round(n / ROUND_TO) * ROUND_TO)


def estimate(service: str, property_size: str, rooms: int, frequency: str) -> tuple[int, int]:
    """Return (low, high) estimated price in NGN per visit. Raises ValueError on bad input."""
    if service not in SERVICES:
        raise ValueError("Unknown service")
    if property_size not in PROPERTY_SIZES:
        raise ValueError("Unknown property size")
    if frequency not in FREQUENCIES:
        raise ValueError("Unknown frequency")
    p = PRICING[service]
    base = p["base"][property_size] + p["per_room"] * max(rooms - 1, 0)
    base *= 1 - RECURRING_DISCOUNT[frequency]
    return _round(base * RANGE_LOW), _round(base * RANGE_HIGH)
