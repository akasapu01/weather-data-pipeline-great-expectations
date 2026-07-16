"""Application settings, loaded from environment / .env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- GCP / BigQuery ---
    gcp_project_id: str = "your-gcp-project"
    gcp_location: str = "US"
    bigquery_dataset: str = "weather_analytics"
    bigquery_raw_dataset: str = "raw_weather"

    # --- Google Cloud Storage staging ---
    gcs_bucket: str = "weather-pipeline-data"
    gcs_staging_prefix: str = "raw"
    google_application_credentials: str = ""

    # --- Alerting / orchestration ---
    slack_webhook_url: str = ""
    prefect_api_url: str = "http://localhost:4200/api"

    # --- Open-Meteo API ---
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    request_timeout_seconds: int = 30

    # --- Local mode: write parquet locally and skip GCS/BigQuery ---
    local_output_dir: str = "data/local"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
