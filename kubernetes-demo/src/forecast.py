"""Simple statistical baseline forecast: average of the last 5 working days.

This is explicitly NOT a machine-learning forecast. It is the arithmetic mean
of the most recent 5 working-day rates available in the database for a given
currency, and it never fabricates missing values or looks at future data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

REQUIRED_HISTORY_DAYS: int = 5

INSUFFICIENT_HISTORY_MESSAGE = "Недостаточно исторических данных"


@dataclass(frozen=True, slots=True)
class RatePoint:
    """A single (date, rate) observation used for forecasting."""

    rate_date: date
    rate: float


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Outcome of a forecast attempt for one currency."""

    currency: str
    forecast_rate: float | None
    forecast_date: date | None
    message: str | None


def is_working_day(day: date) -> bool:
    """Return True for Mon-Fri. Holidays are out of scope for this baseline."""
    return day.weekday() < 5


def next_working_day(after: date) -> date:
    """Return the next working day strictly after `after`."""
    candidate = after + timedelta(days=1)
    while not is_working_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _dedupe_last_per_day(points: Sequence[RatePoint]) -> list[RatePoint]:
    """Collapse duplicate records for the same date, keeping one point per date."""
    by_date: dict[date, RatePoint] = {}
    for point in points:
        by_date[point.rate_date] = point
    return sorted(by_date.values(), key=lambda p: p.rate_date)


def forecast_next_working_day(currency: str, history: Sequence[RatePoint]) -> ForecastResult:
    """Compute forecast = average(rate) over the last 5 distinct working days.

    `history` may be unsorted, contain duplicates, weekends, or None-free
    values; only genuine working-day observations count toward the 5-day
    window. Returns a friendly message instead of a forecast when there is
    not enough history.
    """
    working_points = [p for p in history if p is not None and is_working_day(p.rate_date)]
    deduped = _dedupe_last_per_day(working_points)

    if len(deduped) < REQUIRED_HISTORY_DAYS:
        return ForecastResult(
            currency=currency,
            forecast_rate=None,
            forecast_date=None,
            message=INSUFFICIENT_HISTORY_MESSAGE,
        )

    last_five = deduped[-REQUIRED_HISTORY_DAYS:]
    average_rate = sum(p.rate for p in last_five) / REQUIRED_HISTORY_DAYS
    forecast_date = next_working_day(deduped[-1].rate_date)

    return ForecastResult(
        currency=currency,
        forecast_rate=round(average_rate, 4),
        forecast_date=forecast_date,
        message=None,
    )
