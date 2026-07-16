"""Data-quality validation for weather records.

These checks mirror a Great Expectations suite (expect_column_values_to_not_be_null,
expect_column_values_to_be_between, expect_column_values_to_be_unique, ...) but are
implemented in pure Python over a list of record dicts so the suite runs anywhere
— in unit tests, in the Prefect flow, or in CI — without a configured GE context.
Swap in a full `great_expectations` Checkpoint here if you want the HTML Data Docs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ExpectationResult:
    expectation: str
    column: Optional[str]
    success: bool
    details: str = ""


@dataclass
class ValidationResult:
    evaluated_rows: int
    results: List[ExpectationResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def failed(self) -> List[ExpectationResult]:
        return [r for r in self.results if not r.success]

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.success)
        return f"{passed}/{len(self.results)} expectations passed over {self.evaluated_rows} rows"


# Bounds are inclusive [low, high]; None means unbounded on that side.
RANGE_CHECKS: Dict[str, tuple] = {
    "temperature_c": (-90.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "wind_speed_kmh": (0.0, None),
    "precipitation_mm": (0.0, None),
}
NOT_NULL_COLUMNS = ["city", "country", "observed_at", "extracted_at", "temperature_c"]
UNIQUE_KEY = ("city", "observed_at")


class WeatherDataValidator:
    def validate(self, records: List[Dict[str, Any]]) -> ValidationResult:
        result = ValidationResult(evaluated_rows=len(records))

        # expect_table_row_count_to_be_greater_than(0)
        result.results.append(
            ExpectationResult(
                "expect_table_row_count_to_be_greater_than_0",
                None,
                len(records) > 0,
                f"{len(records)} rows",
            )
        )

        for col in NOT_NULL_COLUMNS:
            result.results.append(self._not_null(records, col))

        for col, (low, high) in RANGE_CHECKS.items():
            result.results.append(self._between(records, col, low, high))

        result.results.append(self._unique(records, UNIQUE_KEY))
        return result

    @staticmethod
    def _not_null(records, col) -> ExpectationResult:
        bad = sum(1 for r in records if r.get(col) is None)
        return ExpectationResult(
            "expect_column_values_to_not_be_null", col, bad == 0, f"{bad} nulls"
        )

    @staticmethod
    def _between(records, col, low, high) -> ExpectationResult:
        def out_of_range(v: Any) -> bool:
            if v is None:  # nulls handled by the not-null check
                return False
            if low is not None and v < low:
                return True
            if high is not None and v > high:
                return True
            return False

        bad = sum(1 for r in records if out_of_range(r.get(col)))
        return ExpectationResult(
            "expect_column_values_to_be_between",
            col,
            bad == 0,
            f"{bad} out of [{low}, {high}]",
        )

    @staticmethod
    def _unique(records, key) -> ExpectationResult:
        seen = set()
        dupes = 0
        for r in records:
            k = tuple(r.get(c) for c in key)
            if k in seen:
                dupes += 1
            seen.add(k)
        return ExpectationResult(
            "expect_compound_columns_to_be_unique",
            "+".join(key),
            dupes == 0,
            f"{dupes} duplicate {key} pairs",
        )


def validate_records(records: List[Dict[str, Any]]) -> ValidationResult:
    return WeatherDataValidator().validate(records)
