from datetime import date

from src.forecast import (
    INSUFFICIENT_HISTORY_MESSAGE,
    RatePoint,
    forecast_next_working_day,
    is_working_day,
    next_working_day,
)


def test_is_working_day() -> None:
    assert is_working_day(date(2026, 9, 18)) is True   # Friday
    assert is_working_day(date(2026, 9, 19)) is False  # Saturday
    assert is_working_day(date(2026, 9, 20)) is False  # Sunday


def test_next_working_day_skips_weekend() -> None:
    assert next_working_day(date(2026, 9, 18)) == date(2026, 9, 21)  # Fri -> Mon


def test_forecast_insufficient_history_returns_message() -> None:
    history = [
        RatePoint(date(2026, 9, 14), 92.0),
        RatePoint(date(2026, 9, 15), 92.5),
    ]
    result = forecast_next_working_day("USD", history)
    assert result.forecast_rate is None
    assert result.message == INSUFFICIENT_HISTORY_MESSAGE


def test_forecast_computes_average_of_last_five_working_days() -> None:
    history = [
        RatePoint(date(2026, 9, 14), 90.0),
        RatePoint(date(2026, 9, 15), 91.0),
        RatePoint(date(2026, 9, 16), 92.0),
        RatePoint(date(2026, 9, 17), 93.0),
        RatePoint(date(2026, 9, 18), 94.0),
    ]
    result = forecast_next_working_day("USD", history)
    assert result.forecast_rate == 92.0
    assert result.forecast_date == date(2026, 9, 21)
    assert result.message is None


def test_forecast_ignores_weekend_points_and_duplicates() -> None:
    history = [
        RatePoint(date(2026, 9, 12), 89.0),  # Saturday -- excluded
        RatePoint(date(2026, 9, 14), 90.0),
        RatePoint(date(2026, 9, 14), 90.5),  # duplicate date -- last one wins
        RatePoint(date(2026, 9, 15), 91.0),
        RatePoint(date(2026, 9, 16), 92.0),
        RatePoint(date(2026, 9, 17), 93.0),
        RatePoint(date(2026, 9, 18), 94.0),
    ]
    result = forecast_next_working_day("USD", history)
    assert result.forecast_rate == (90.5 + 91.0 + 92.0 + 93.0 + 94.0) / 5
