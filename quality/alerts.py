"""Slack alerting for data-quality failures."""

from __future__ import annotations

from typing import Optional

import structlog

from quality.validator import ValidationResult

log = structlog.get_logger(__name__)


def _format_message(result: ValidationResult) -> str:
    lines = [
        ":rotating_light: *Weather pipeline data-quality check failed*",
        f"> {result.summary()}",
    ]
    for r in result.failed:
        col = f" `{r.column}`" if r.column else ""
        lines.append(f"• *{r.expectation}*{col} — {r.details}")
    return "\n".join(lines)


def send_quality_alert(
    result: ValidationResult, webhook_url: Optional[str] = None
) -> bool:
    """Post a Slack alert if the validation failed.

    Returns True if an alert was sent, False otherwise (passing check, or no
    webhook configured). Never raises — alerting must not break the pipeline.
    """
    if result.success:
        log.info("quality_check_passed", summary=result.summary())
        return False

    message = _format_message(result)
    if not webhook_url:
        log.warning("quality_check_failed_no_webhook", summary=result.summary())
        return False

    try:
        import requests

        resp = requests.post(webhook_url, json={"text": message}, timeout=10)
        resp.raise_for_status()
        log.info("quality_alert_sent", status=resp.status_code)
        return True
    except Exception as exc:  # pragma: no cover - network path
        log.error("quality_alert_failed", error=str(exc))
        return False
