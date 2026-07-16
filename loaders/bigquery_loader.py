"""Load staged NDJSON from GCS into a BigQuery raw table."""

from __future__ import annotations

import structlog

log = structlog.get_logger(__name__)

RAW_TABLE = "hourly_observations"


class BigQueryLoader:
    def __init__(self, project: str, dataset: str, location: str = "US"):
        self.project = project
        self.dataset = dataset
        self.location = location
        self._client = None

    @property
    def client(self):
        # Lazy import keeps the module importable without google-cloud-bigquery.
        if self._client is None:
            from google.cloud import bigquery

            self._client = bigquery.Client(project=self.project, location=self.location)
        return self._client

    def ensure_dataset(self) -> None:
        from google.cloud import bigquery
        from google.api_core.exceptions import Conflict

        ds_id = f"{self.project}.{self.dataset}"
        dataset = bigquery.Dataset(ds_id)
        dataset.location = self.location
        try:
            self.client.create_dataset(dataset)
            log.info("created_dataset", dataset=ds_id)
        except Conflict:
            log.info("dataset_exists", dataset=ds_id)

    def load_ndjson_from_gcs(self, gcs_uri: str, table: str = RAW_TABLE) -> int:
        """Load a newline-delimited JSON file from GCS, autodetecting schema.

        Returns the number of rows in the destination table after the load.
        """
        from google.cloud import bigquery

        self.ensure_dataset()
        table_id = f"{self.project}.{self.dataset}.{table}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
        )
        job = self.client.load_table_from_uri(
            gcs_uri, table_id, job_config=job_config
        )
        job.result()  # wait for completion
        dest = self.client.get_table(table_id)
        log.info("loaded_bigquery", table=table_id, rows=dest.num_rows)
        return dest.num_rows
