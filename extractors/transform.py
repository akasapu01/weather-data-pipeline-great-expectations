"""Pure, dependency-free normalization of Open-Meteo API responses.

Kept free of third-party imports so it can be unit-tested in isolation and
reused by the httpx-based extractor.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# The hourly variables we request from Open-Meteo, mapped to output column names.
HOURLY_VARIABLES = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "wind_speed_10m": "wind_speed_kmh",
    "precipitation": "precipitation_mm",
}


def normalize_response(
    city_name: str,
    country: str,
    latitude: float,
    longitude: float,
    payload: Dict[str, Any],
    extracted_at: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Flatten one Open-Meteo forecast response into a list of hourly rows.

    Each row is one (city, timestamp) observation. Raises ValueError if the
    payload is missing the expected `hourly` block or the time axis.
    """
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or "time" not in hourly:
        raise ValueError(f"Malformed Open-Meteo payload for {city_name}: no hourly.time")

    times = hourly["time"]
    if extracted_at is None:
        extracted_at = datetime.now(timezone.utc).isoformat()

    rows: List[Dict[str, Any]] = []
    for i, ts in enumerate(times):
        row: Dict[str, Any] = {
            "city": city_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "observed_at": ts,
            "extracted_at": extracted_at,
        }
        for api_key, out_key in HOURLY_VARIABLES.items():
            series = hourly.get(api_key) or []
            row[out_key] = series[i] if i < len(series) else None
        rows.append(row)
    return rows


def records_to_ndjson(records: List[Dict[str, Any]]) -> str:
    """Serialize records to newline-delimited JSON (BigQuery load format)."""
    import json

    return "\n".join(json.dumps(r, separators=(",", ":")) for r in records)
