"""Integration test: fetch (mocked HTTP) -> validate -> upsert (mongomock) -> forecast.

Runs entirely in-process with mocked network/DB, so it needs no live CBR
endpoint or MongoDB instance. Marked so real infra-backed variants can be
added later without breaking CI (see docs/cloud/README.md "Testing against
real infrastructure").
"""

from __future__ import annotations

from datetime import date
from unittest.mock import Mock, patch

import mongomock
import pytest

from src.cbr_client import fetch_cbr_rates
from src.forecast import forecast_next_working_day
from src.mongo_repository import RatesRepository
from tests.unit.test_cbr_client import VALID_XML


def _mock_response(xml_text: str) -> Mock:
    response = Mock()
    response.status_code = 200
    response.content = xml_text.encode("windows-1251")
    response.encoding = "windows-1251"
    return response


@pytest.fixture
def repo() -> RatesRepository:
    repository = RatesRepository.__new__(RatesRepository)
    repository._uri = "mongodb://localhost:27017"
    repository._database_name = "currency"
    repository._collection_name = "rates"
    repository._client = mongomock.MongoClient()
    repository.ensure_indexes()
    return repository


def test_fetch_validate_persist_roundtrip(repo: RatesRepository) -> None:
    with patch("src.cbr_client.requests.get", return_value=_mock_response(VALID_XML)):
        rates = fetch_cbr_rates()

    rows = [
        {
            "date": rate.rate_date.isoformat(),
            "currency": rate.currency,
            "nominal": rate.nominal,
            "rate": rate.rate,
            "source": rate.source,
        }
        for rate in rates
    ]
    repo.upsert_rates(rows)

    stored = repo.latest_rate("USD")
    assert stored is not None
    assert stored["rate"] == pytest.approx(92.5)


def test_repeated_run_is_idempotent(repo: RatesRepository) -> None:
    with patch("src.cbr_client.requests.get", return_value=_mock_response(VALID_XML)):
        rates = fetch_cbr_rates()
    rows = [
        {
            "date": r.rate_date.isoformat(),
            "currency": r.currency,
            "nominal": r.nominal,
            "rate": r.rate,
        }
        for r in rates
    ]

    repo.upsert_rates(rows)
    repo.upsert_rates(rows)  # second run, same date -- must not duplicate

    assert repo._collection().count_documents({}) == 3  # USD, EUR, CNY -- one each


def test_forecast_reports_insufficient_history_before_five_days(repo: RatesRepository) -> None:
    repo.upsert_rates(
        [{"date": "2026-09-17", "currency": "USD", "nominal": 1, "rate": 92.5}]
    )
    history = repo.last_working_day_rates("USD", limit=5)
    result = forecast_next_working_day("USD", history)
    assert result.forecast_rate is None
    assert result.message is not None


def test_forecast_after_five_working_days_of_history(repo: RatesRepository) -> None:
    for day, rate in [
        ("2026-09-14", 90.0),
        ("2026-09-15", 91.0),
        ("2026-09-16", 92.0),
        ("2026-09-17", 93.0),
        ("2026-09-18", 94.0),
    ]:
        repo.upsert_rates([{"date": day, "currency": "USD", "nominal": 1, "rate": rate}])
    history = repo.last_working_day_rates("USD", limit=5)
    result = forecast_next_working_day("USD", history)
    assert result.forecast_rate == 92.0
    assert result.forecast_date == date(2026, 9, 21)
