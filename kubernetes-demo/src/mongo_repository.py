"""MongoDB persistence layer for currency rates.

Provides an idempotent upsert (unique key: date + currency) and a query for
the last N working-day rates per currency, used by both the PySpark job and
the Streamlit app. Connection details always come from environment
variables / Kubernetes Secrets -- never hardcoded.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Any

from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.errors import PyMongoError

from src.forecast import RatePoint
from src.logging_config import get_logger

logger = get_logger("mongo_repository")

DEFAULT_DATABASE = "currency"
DEFAULT_COLLECTION = "rates"
DEFAULT_CONNECT_TIMEOUT_MS = 5000
DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 5000


class MongoConnectionError(Exception):
    """Raised when MongoDB cannot be reached within the configured timeout."""


def _env_or_default(name: str, default: str) -> str:
    return os.environ.get(name, default)


class RatesRepository:
    """Repository for the `rates` collection: {date, currency, nominal, rate, source, loaded_at}."""

    def __init__(
        self,
        uri: str | None = None,
        database: str | None = None,
        collection: str | None = None,
        connect_timeout_ms: int = DEFAULT_CONNECT_TIMEOUT_MS,
    ) -> None:
        self._uri = uri or os.environ.get("MONGODB_URI")
        if not self._uri:
            raise MongoConnectionError("MONGODB_URI is not configured")
        self._database_name = database or _env_or_default("MONGODB_DATABASE", DEFAULT_DATABASE)
        self._collection_name = collection or _env_or_default(
            "MONGODB_COLLECTION", DEFAULT_COLLECTION
        )
        self._client: MongoClient[dict[str, Any]] = MongoClient(
            self._uri,
            connectTimeoutMS=connect_timeout_ms,
            serverSelectionTimeoutMS=DEFAULT_SERVER_SELECTION_TIMEOUT_MS,
        )

    def ensure_indexes(self) -> None:
        """Create the unique (date, currency) index used for idempotent upserts."""
        try:
            self._collection().create_index(
                [("date", ASCENDING), ("currency", ASCENDING)],
                unique=True,
                name="date_currency_unique",
            )
        except PyMongoError as exc:
            raise MongoConnectionError(f"Failed to create index: {exc}") from exc

    def _collection(self):  # type: ignore[no-untyped-def]
        return self._client[self._database_name][self._collection_name]

    def upsert_rates(self, rows: list[dict[str, Any]]) -> int:
        """Idempotently upsert rate documents keyed on (date, currency).

        Returns the number of documents matched or inserted. Re-running with
        the same date/currency never creates duplicates.
        """
        if not rows:
            return 0
        operations = []
        for row in rows:
            key = {"date": row["date"], "currency": row["currency"]}
            document = {
                **key,
                "nominal": row["nominal"],
                "rate": row["rate"],
                "source": row.get("source", "cbr.ru"),
                "loaded_at": row.get("loaded_at", datetime.now(UTC).isoformat()),
            }
            operations.append(UpdateOne(key, {"$set": document}, upsert=True))
        try:
            result = self._collection().bulk_write(operations, ordered=False)
        except PyMongoError as exc:
            raise MongoConnectionError(f"Upsert failed: {exc}") from exc
        return result.upserted_count + result.modified_count + result.matched_count

    def last_working_day_rates(self, currency: str, limit: int = 5) -> list[RatePoint]:
        """Return up to `limit` most recent rate points for `currency`, oldest first."""
        try:
            cursor = (
                self._collection()
                .find({"currency": currency})
                .sort("date", -1)
                .limit(limit)
            )
            docs = list(cursor)
        except PyMongoError as exc:
            raise MongoConnectionError(f"Query failed: {exc}") from exc

        points = [
            RatePoint(rate_date=_parse_date(doc["date"]), rate=float(doc["rate"])) for doc in docs
        ]
        return sorted(points, key=lambda p: p.rate_date)

    def latest_rate(self, currency: str) -> dict[str, Any] | None:
        """Return the most recent single rate document for `currency`, or None."""
        try:
            return self._collection().find_one({"currency": currency}, sort=[("date", -1)])
        except PyMongoError as exc:
            raise MongoConnectionError(f"Query failed: {exc}") from exc

    def ping(self) -> bool:
        """Cheap connectivity check used by Streamlit for graceful degradation."""
        try:
            self._client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def close(self) -> None:
        self._client.close()


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()
