"""Stage raw weather data to Google Cloud Storage."""

from __future__ import annotations

import structlog

log = structlog.get_logger(__name__)


class GCSLoader:
    def __init__(self, bucket: str, project: str, prefix: str = "raw"):
        self.bucket_name = bucket
        self.project = project
        self.prefix = prefix.strip("/")
        self._client = None

    @property
    def client(self):
        # Imported lazily so the module is importable without GCP libs installed.
        if self._client is None:
            from google.cloud import storage

            self._client = storage.Client(project=self.project)
        return self._client

    def _blob_path(self, name: str) -> str:
        return f"{self.prefix}/{name}" if self.prefix else name

    def upload_string(self, content: str, name: str, content_type: str) -> str:
        """Upload a string as a blob and return its gs:// URI."""
        blob_path = self._blob_path(name)
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(content, content_type=content_type)
        uri = f"gs://{self.bucket_name}/{blob_path}"
        log.info("uploaded_to_gcs", uri=uri, bytes=len(content))
        return uri
