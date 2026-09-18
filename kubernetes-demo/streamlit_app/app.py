"""Streamlit landing page: current CBR rates + 5-working-day baseline forecast.

Reads only from MongoDB (never talks to CBR or runs PySpark directly). Fails
gracefully with a user-facing message when MongoDB is unavailable, and never
surfaces stack traces, connection strings, passwords, or internal
Kubernetes/IP details to the browser.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.forecast import forecast_next_working_day  # noqa: E402
from src.logging_config import get_logger  # noqa: E402
from src.mongo_repository import MongoConnectionError, RatesRepository  # noqa: E402

logger = get_logger("streamlit_app")

CURRENCY_NAMES = {
    "USD": "Доллар США",
    "EUR": "Евро",
    "CNY": "Китайский юань",
}
CURRENCIES = ("USD", "EUR", "CNY")

st.set_page_config(page_title="Курсы валют ЦБ РФ", page_icon="\U0001F4B1", layout="centered")


@st.cache_resource(show_spinner=False)
def get_repository() -> RatesRepository | None:
    """Build the Mongo repository once per session; return None if misconfigured."""
    try:
        return RatesRepository()
    except MongoConnectionError:
        logger.error(
            "Mongo repository init failed",
            extra={"extra_fields": {"error_type": "MongoConnectionError"}},
        )
        return None


def render_current_rates(repo: RatesRepository) -> None:
    st.subheader("Текущие курсы")
    rows = []
    for currency in CURRENCIES:
        doc = repo.latest_rate(currency)
        if doc is None:
            continue
        rows.append(
            {
                "Валюта": currency,
                "Название": CURRENCY_NAMES[currency],
                "Курс": doc["rate"],
                "Дата": doc["date"],
            }
        )
    if not rows:
        st.warning("Данные о курсах пока отсутствуют. Дождитесь первого запуска DAG.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    latest_loaded_at = max(
        (repo.latest_rate(c) or {}).get("loaded_at", "") for c in CURRENCIES
    )
    if latest_loaded_at:
        st.caption(f"Последнее обновление: {latest_loaded_at}")


def render_forecast(repo: RatesRepository) -> None:
    st.subheader("Прогноз курса на следующий рабочий день")
    rows = []
    for currency in CURRENCIES:
        history = repo.last_working_day_rates(currency, limit=5)
        result = forecast_next_working_day(currency, history)
        current = history[-1].rate if history else None
        rows.append(
            {
                "Валюта": currency,
                "Текущий курс": current if current is not None else "\u2014",
                "Прогноз на следующий рабочий день": (
                    result.forecast_rate if result.forecast_rate is not None else result.message
                ),
                "Дата прогноза": (
                    result.forecast_date.isoformat() if result.forecast_date else "\u2014"
                ),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption(
        "Прогноз является простым статистическим baseline и рассчитывается как среднее "
        "значение курса за последние 5 рабочих дней. Он не является финансовой рекомендацией."
    )


def main() -> None:
    st.title("Курсы валют ЦБ РФ")
    repo = get_repository()
    if repo is None:
        st.error(
            "Сервис данных временно недоступен. Попробуйте обновить страницу позже."
        )
        return

    if not repo.ping():
        st.error(
            "Не удалось подключиться к базе данных. Попробуйте обновить страницу позже."
        )
        return

    render_current_rates(repo)
    render_forecast(repo)
    st.caption(f"Страница сгенерирована: {datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
