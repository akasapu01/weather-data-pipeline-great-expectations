"""Prefect flow orchestrating the weather ELT pipeline.

Stages:
  1. Extract hourly weather for all cities from Open-Meteo (no API key needed)
  2. Run data-quality checks; alert to Slack on failure
  3. Stage raw NDJSON to GCS
  4. Load GCS -> BigQuery raw table
  (dbt then transforms raw_weather -> marts; run separately, see README)

Run:
  python flows/weather_pipeline.py            # full run (needs GCP creds)
  python flows/weather_pipeline.py --local    # extract + validate + write local NDJSON
"""

from __future__ import annotations

import sys
from pathlib import Path

import structlog
from prefect import flow, task

# make `config`, `extractors`, etc. importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402
from extractors.open_meteo_extractor import OpenMeteoExtractor  # noqa: E402
from extractors.transform import records_to_ndjson  # noqa: E402
from loaders.bigquery_loader import BigQueryLoader  # noqa: E402
from loaders.gcs_loader import GCSLoader  # noqa: E402
from quality.alerts import send_quality_alert  # noqa: E402
from quality.validator import validate_records  # noqa: E402

log = structlog.get_logger(__name__)


@task(retries=2, retry_delay_seconds=10)
def extract_weather():
    settings = get_settings()
    extractor = OpenMeteoExtractor(
        base_url=settings.open_meteo_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    return extractor.extract()


@task
def run_quality_checks(records):
    settings = get_settings()
    result = validate_records(records)
    log.info("quality_result", summary=result.summary())
    send_quality_alert(result, settings.slack_webhook_url or None)
    if not result.success:
        raise ValueError(f"Data-quality check failed: {result.summary()}")
    return result


@task
def stage_to_gcs(records) -> str:
    settings = get_settings()
    ndjson = records_to_ndjson(records)
    loader = GCSLoader(
        bucket=settings.gcs_bucket,
        project=settings.gcp_project_id,
        prefix=settings.gcs_staging_prefix,
    )
    # a real run would use a run timestamp in the name; kept static-friendly here
    return loader.upload_string(
        ndjson, "hourly_observations.ndjson", "application/x-ndjson"
    )


@task
def load_to_bigquery(gcs_uri: str) -> int:
    settings = get_settings()
    loader = BigQueryLoader(
        project=settings.gcp_project_id,
        dataset=settings.bigquery_raw_dataset,
        location=settings.gcp_location,
    )
    return loader.load_ndjson_from_gcs(gcs_uri)


def _write_local(records) -> str:
    settings = get_settings()
    out_dir = Path(settings.local_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "hourly_observations.ndjson"
    path.write_text(records_to_ndjson(records), encoding="utf-8")
    log.info("wrote_local", path=str(path), rows=len(records))
    return str(path)


@flow(name="weather-data-pipeline")
def weather_pipeline(local: bool = False):
    records = extract_weather()
    run_quality_checks(records)
    if local:
        return _write_local(records)
    gcs_uri = stage_to_gcs(records)
    rows = load_to_bigquery(gcs_uri)
    log.info("pipeline_complete", rows_in_raw_table=rows)
    return gcs_uri


if __name__ == "__main__":
    weather_pipeline(local="--local" in sys.argv)
