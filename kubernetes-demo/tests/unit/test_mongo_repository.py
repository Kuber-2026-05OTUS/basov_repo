from datetime import UTC, date, datetime

import mongomock
import pytest

from src.mongo_repository import MongoConnectionError, RatesRepository


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch) -> RatesRepository:
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    repository = RatesRepository.__new__(RatesRepository)
    repository._uri = "mongodb://localhost:27017"
    repository._database_name = "currency"
    repository._collection_name = "rates"
    repository._client = mongomock.MongoClient()
    return repository


def test_missing_uri_raises() -> None:
    with pytest.raises(MongoConnectionError, match="MONGODB_URI"):
        RatesRepository(uri=None)


def test_upsert_rates_is_idempotent(repo: RatesRepository) -> None:
    row = {
        "date": "2026-09-17",
        "currency": "USD",
        "nominal": 1,
        "rate": 92.5,
        "source": "cbr.ru",
        "loaded_at": datetime.now(UTC).isoformat(),
    }
    repo.ensure_indexes()
    repo.upsert_rates([row])
    repo.upsert_rates([{**row, "rate": 93.0}])  # re-run with updated value

    docs = list(repo._collection().find({"currency": "USD"}))
    assert len(docs) == 1
    assert docs[0]["rate"] == 93.0


def test_last_working_day_rates_sorted_oldest_first(repo: RatesRepository) -> None:
    repo.ensure_indexes()
    for day, rate in [("2026-09-14", 90.0), ("2026-09-15", 91.0), ("2026-09-16", 92.0)]:
        repo.upsert_rates(
            [
                {
                    "date": day,
                    "currency": "EUR",
                    "nominal": 1,
                    "rate": rate,
                    "source": "cbr.ru",
                }
            ]
        )
    points = repo.last_working_day_rates("EUR", limit=5)
    assert [p.rate_date for p in points] == [
        date(2026, 9, 14),
        date(2026, 9, 15),
        date(2026, 9, 16),
    ]


def test_ensure_indexes_enforces_uniqueness(repo: RatesRepository) -> None:
    repo.ensure_indexes()
    indexes = repo._collection().index_information()
    assert "date_currency_unique" in indexes
