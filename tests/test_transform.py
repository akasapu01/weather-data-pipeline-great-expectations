"""Unit tests for the pure Open-Meteo normalization layer."""

from extractors.transform import (
    HOURLY_VARIABLES,
    normalize_response,
    records_to_ndjson,
)

SAMPLE_PAYLOAD = {
    "latitude": 40.71,
    "longitude": -74.0,
    "hourly": {
        "time": ["2026-07-17T00:00", "2026-07-17T01:00"],
        "temperature_2m": [21.4, 20.9],
        "relative_humidity_2m": [65, 68],
        "wind_speed_10m": [12.0, 9.5],
        "precipitation": [0.0, 0.2],
    },
}


def test_normalize_produces_one_row_per_hour():
    rows = normalize_response("New York", "US", 40.71, -74.0, SAMPLE_PAYLOAD,
                              extracted_at="2026-07-17T02:00:00Z")
    assert len(rows) == 2
    first = rows[0]
    assert first["city"] == "New York"
    assert first["country"] == "US"
    assert first["observed_at"] == "2026-07-17T00:00"
    assert first["temperature_c"] == 21.4
    assert first["humidity_pct"] == 65
    assert first["wind_speed_kmh"] == 12.0
    assert first["precipitation_mm"] == 0.0
    assert first["extracted_at"] == "2026-07-17T02:00:00Z"


def test_normalize_maps_all_configured_variables():
    rows = normalize_response("Paris", "FR", 48.85, 2.35, SAMPLE_PAYLOAD)
    for out_key in HOURLY_VARIABLES.values():
        assert out_key in rows[0]


def test_normalize_handles_missing_series_as_none():
    payload = {"hourly": {"time": ["2026-07-17T00:00"], "temperature_2m": []}}
    rows = normalize_response("X", "US", 1.0, 2.0, payload)
    assert rows[0]["temperature_c"] is None
    assert rows[0]["humidity_pct"] is None


def test_normalize_rejects_malformed_payload():
    import pytest

    with pytest.raises(ValueError):
        normalize_response("X", "US", 1.0, 2.0, {"nope": True})


def test_records_to_ndjson_is_line_delimited():
    rows = normalize_response("New York", "US", 40.71, -74.0, SAMPLE_PAYLOAD)
    ndjson = records_to_ndjson(rows)
    lines = ndjson.splitlines()
    assert len(lines) == 2
    import json

    assert json.loads(lines[0])["city"] == "New York"
