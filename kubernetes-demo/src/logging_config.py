"""Structured JSON logging shared by every Python component (DAG, Spark job, Streamlit).

Never log secrets: passwords, tokens, MongoDB URIs, cookies, or Authorization headers.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

_SENSITIVE_KEYS = {"password", "token", "uri", "authorization", "secret", "cookie"}


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON with timestamp/level/service/message."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "message": record.getMessage(),
        }
        if record.exc_info:
            exc_type = record.exc_info[0]
            payload["error_type"] = exc_type.__name__ if exc_type else "Exception"
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                if key.lower() in _SENSITIVE_KEYS:
                    continue
                payload[key] = value
        return json.dumps(payload, default=str, ensure_ascii=False)


def get_logger(service: str, level: str | None = None) -> logging.Logger:
    """Return a configured, idempotent structured logger for a given service name."""
    logger = logging.getLogger(service)
    log_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JsonFormatter(service))
        logger.addHandler(handler)
        logger.propagate = False
    return logger
