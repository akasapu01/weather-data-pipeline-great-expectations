"""Static list of cities to collect weather for.

Kept dependency-free so it can be imported by the pure transform/validation
layers (and their tests) without pulling in pydantic or httpx.
"""

from typing import NamedTuple


class City(NamedTuple):
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


CITIES = [
    City("New York", "US", 40.7128, -74.0060, "America/New_York"),
    City("Los Angeles", "US", 34.0522, -118.2437, "America/Los_Angeles"),
    City("Chicago", "US", 41.8781, -87.6298, "America/Chicago"),
    City("London", "GB", 51.5074, -0.1278, "Europe/London"),
    City("Paris", "FR", 48.8566, 2.3522, "Europe/Paris"),
    City("Berlin", "DE", 52.5200, 13.4050, "Europe/Berlin"),
    City("Tokyo", "JP", 35.6762, 139.6503, "Asia/Tokyo"),
    City("Sydney", "AU", -33.8688, 151.2093, "Australia/Sydney"),
    City("Mumbai", "IN", 19.0760, 72.8777, "Asia/Kolkata"),
    City("Singapore", "SG", 1.3521, 103.8198, "Asia/Singapore"),
    City("Toronto", "CA", 43.6532, -79.3832, "America/Toronto"),
    City("Dubai", "AE", 25.2048, 55.2708, "Asia/Dubai"),
]
