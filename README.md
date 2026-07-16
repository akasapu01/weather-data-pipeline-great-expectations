# Weather Data Pipeline with Data-Quality Checks

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Prefect](https://img.shields.io/badge/Prefect-2.14-070E10?logo=prefect)
![BigQuery](https://img.shields.io/badge/BigQuery-Warehouse-4285F4?logo=googlebigquery)
![dbt](https://img.shields.io/badge/dbt-1.7-orange?logo=dbt)
![Data Quality](https://img.shields.io/badge/Data%20Quality-Great%20Expectations%20style-FF6310)

An ELT pipeline that pulls hourly weather for a set of global cities from the free
**Open-Meteo API** (no key required), runs **data-quality checks**, stages the raw
data to **Google Cloud Storage**, loads it into **BigQuery**, and transforms it with
**dbt** into an analytics-ready daily fact table. **Prefect** orchestrates the run.

## Architecture

```
Open-Meteo API  ──httpx──▶  Python extractor  ──▶  Data-quality checks ──▶ Slack alert (on fail)
(hourly, no key)             (normalize rows)         (Great-Expectations-style suite)
                                    │
                                    ▼
                        GCS raw zone (NDJSON)  ──▶  BigQuery raw_weather.hourly_observations
                                                              │
                                                              ▼
                                       dbt: stg_hourly_observations ──▶ fct_weather_city_daily
                                                              │
                                                              ▼
                                            BI / analytics (Looker Studio, etc.)

              Orchestration: Prefect flow  ·  Alerting: Slack webhook
```

## Tech stack

| Layer | Technology |
|-------|------------|
| Extraction | Python 3.11, httpx (async-capable), tenacity (retries) |
| Data quality | Great-Expectations-style suite (pure-Python, see note below) |
| Staging | Google Cloud Storage (NDJSON) |
| Warehouse | BigQuery |
| Transformation | dbt Core 1.7 + dbt-bigquery, dbt_utils, dbt_expectations |
| Orchestration | Prefect 2.14 |
| Config | pydantic-settings |
| Alerting | Slack webhook |
| Logging | structlog |

## Project structure

```
config/            # pydantic settings + static city list
extractors/
  transform.py     # pure normalization (unit-tested, no third-party deps)
  open_meteo_extractor.py   # httpx client with retries + rate limiting
loaders/
  gcs_loader.py    # stage NDJSON to GCS
  bigquery_loader.py        # load GCS -> BigQuery raw table
quality/
  validator.py     # data-quality expectations (pure, testable)
  alerts.py        # Slack alerting on failure
flows/
  weather_pipeline.py       # Prefect flow (pipeline entrypoint)
dbt_project/       # staging + marts models, sources, tests
tests/             # pytest unit tests (extractor + validator)
Dockerfile
requirements.txt
```

> **Note on Great Expectations:** the quality suite in `quality/validator.py` expresses
> the same expectations as a Great Expectations suite
> (`expect_column_values_to_not_be_null`, `expect_column_values_to_be_between`,
> `expect_compound_columns_to_be_unique`, …) but is implemented in pure Python so it
> runs in unit tests and CI without a configured GE context. Point the same stage at a
> `great_expectations` Checkpoint if you want the HTML Data Docs. The dbt layer also
> ships `dbt_expectations` tests for the warehouse-side equivalent.

## Setup

### Prerequisites
- Python 3.11+
- (Full run only) a GCP project, a service-account JSON, a GCS bucket, and BigQuery access

### 1. Install
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in GCP project / bucket / credentials for a full run
```

### 2. Run the pipeline

**Local mode** — extract + validate + write NDJSON locally, no GCP needed:
```bash
python flows/weather_pipeline.py --local
# -> writes data/local/hourly_observations.ndjson
```

**Full mode** — stage to GCS and load into BigQuery (needs `.env` + credentials):
```bash
python flows/weather_pipeline.py
```

Or via Docker:
```bash
docker build -t weather-pipeline .
docker run --env-file .env weather-pipeline
```

### 3. Transform with dbt
```bash
cd dbt_project
dbt deps
dbt run          # builds staging + fct_weather_city_daily
dbt test         # runs not_null / range / uniqueness expectations
```

## Tests
```bash
pytest -q        # unit tests for the extractor transform and the quality suite
```

## Maintainer
**Jyothi Sree** — Senior Data Engineer
- Email: Jyothisree.work@gmail.com
- LinkedIn: https://www.linkedin.com/in/jyothisree123/
