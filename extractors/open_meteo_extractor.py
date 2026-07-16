"""Extract hourly weather observations from the free Open-Meteo API.

Open-Meteo requires no API key, so this extractor runs out of the box. It fetches
one forecast day of hourly data for each configured city, with retries and rate
limiting, and returns normalized rows via extractors.transform.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.cities import CITIES, City
from extractors.transform import HOURLY_VARIABLES, normalize_response

log = structlog.get_logger(__name__)


class OpenMeteoExtractor:
    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        timeout_seconds: int = 30,
        forecast_days: int = 1,
        rate_limit_seconds: float = 0.2,
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.forecast_days = forecast_days
        self.rate_limit_seconds = rate_limit_seconds

    def _params(self, city: City) -> Dict[str, Any]:
        return {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "hourly": ",".join(HOURLY_VARIABLES.keys()),
            "forecast_days": self.forecast_days,
            "timezone": "UTC",
        }

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(
            (httpx.HTTPStatusError, httpx.TransportError)
        ),
        reraise=True,
    )
    def _fetch_city(self, client: httpx.Client, city: City) -> List[Dict[str, Any]]:
        resp = client.get(self.base_url, params=self._params(city))
        resp.raise_for_status()
        rows = normalize_response(
            city.name, city.country, city.latitude, city.longitude, resp.json()
        )
        log.info("extracted_city", city=city.name, rows=len(rows))
        return rows

    def extract(self, cities: List[City] | None = None) -> List[Dict[str, Any]]:
        """Fetch and normalize hourly weather for all cities."""
        cities = cities or CITIES
        all_rows: List[Dict[str, Any]] = []
        with httpx.Client(timeout=self.timeout_seconds) as client:
            for city in cities:
                all_rows.extend(self._fetch_city(client, city))
                time.sleep(self.rate_limit_seconds)  # be polite to the free API
        log.info("extraction_complete", cities=len(cities), rows=len(all_rows))
        return all_rows
