"""Unit tests for the data-quality validator."""

from quality.validator import validate_records, WeatherDataValidator


def _good_row(**overrides):
    row = {
        "city": "New York",
        "country": "US",
        "latitude": 40.71,
        "longitude": -74.0,
        "observed_at": "2026-07-17T00:00",
        "extracted_at": "2026-07-17T02:00:00Z",
        "temperature_c": 21.4,
        "humidity_pct": 65.0,
        "wind_speed_kmh": 12.0,
        "precipitation_mm": 0.0,
    }
    row.update(overrides)
    return row


def test_clean_data_passes_all_expectations():
    records = [
        _good_row(observed_at="2026-07-17T00:00"),
        _good_row(observed_at="2026-07-17T01:00"),
    ]
    result = validate_records(records)
    assert result.success, result.summary()
    assert result.failed == []


def test_empty_data_fails_row_count():
    result = validate_records([])
    assert not result.success
    assert any("row_count" in r.expectation for r in result.failed)


def test_null_temperature_fails_not_null():
    result = validate_records([_good_row(temperature_c=None)])
    assert not result.success
    failed = [r for r in result.failed if r.column == "temperature_c"]
    assert any(r.expectation == "expect_column_values_to_not_be_null" for r in failed)


def test_out_of_range_humidity_fails_between():
    result = validate_records([_good_row(humidity_pct=150.0)])
    assert not result.success
    assert any(
        r.expectation == "expect_column_values_to_be_between"
        and r.column == "humidity_pct"
        for r in result.failed
    )


def test_negative_precipitation_fails():
    result = validate_records([_good_row(precipitation_mm=-1.0)])
    assert not result.success


def test_duplicate_city_timestamp_fails_uniqueness():
    dup = _good_row(observed_at="2026-07-17T00:00")
    result = validate_records([dup, dict(dup)])
    assert not result.success
    assert any("unique" in r.expectation for r in result.failed)


def test_summary_counts_expectations():
    result = WeatherDataValidator().validate([_good_row()])
    assert "over 1 rows" in result.summary()
