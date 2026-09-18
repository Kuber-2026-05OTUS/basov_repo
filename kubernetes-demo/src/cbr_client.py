"""Client for the Central Bank of Russia (CBR) daily currency rates XML feed.

Handles HTTP timeouts/retries with exponential backoff, validates the response
structure, and extracts USD/EUR/CNY rates without ever using eval()/exec()
or shell commands.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET  # nosec B405 -- trusted CBR government feed, not arbitrary user XML
from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

import requests

from src.logging_config import get_logger

logger = get_logger("cbr_client")

DEFAULT_CBR_ENDPOINT: Final[str] = "https://www.cbr.ru/scripts/XML_daily.asp"
REQUIRED_CURRENCIES: Final[frozenset[str]] = frozenset({"USD", "EUR", "CNY"})
MAX_RETRIES: Final[int] = 3
BASE_BACKOFF_SECONDS: Final[float] = 5.0
REQUEST_TIMEOUT_SECONDS: Final[float] = 15.0


class CbrClientError(Exception):
    """Raised for any unrecoverable CBR fetch/validation failure."""


class CbrValidationError(CbrClientError):
    """Raised when the CBR response is malformed or missing required data."""


class CbrHttpError(CbrClientError):
    """Raised when the CBR endpoint is unreachable or returns an HTTP error."""


@dataclass(frozen=True, slots=True)
class CurrencyRate:
    """A single normalized currency rate record."""

    currency: str
    nominal: int
    rate: float
    rate_date: date
    source: str = "cbr.ru"


def _parse_cbr_date(raw_date: str) -> date:
    """Parse CBR's `DD.MM.YYYY` date attribute into a `date`."""
    try:
        return datetime.strptime(raw_date, "%d.%m.%Y").date()
    except ValueError as exc:
        raise CbrValidationError(f"Unparseable CBR date attribute: {raw_date!r}") from exc


def parse_cbr_xml(xml_bytes: bytes) -> list[CurrencyRate]:
    """Parse CBR `XML_daily.asp` payload and return rates for USD/EUR/CNY.

    Raises `CbrValidationError` on malformed XML, missing required currencies,
    or impossible values (non-positive nominal/rate).
    """
    try:
        # CBR's public XML_daily.asp feed is a fixed, well-known government
        # source (not arbitrary user input); stdlib ElementTree is used
        # deliberately to avoid an extra dependency for this trusted feed.
        root = ET.fromstring(xml_bytes)  # noqa: S314  # nosec B314
    except ET.ParseError as exc:
        raise CbrValidationError(f"Malformed CBR XML response: {exc}") from exc

    if root.tag != "ValCurs":
        raise CbrValidationError(f"Unexpected root element: {root.tag!r}")

    raw_date = root.attrib.get("Date")
    if not raw_date:
        raise CbrValidationError("CBR response missing Date attribute")
    rate_date = _parse_cbr_date(raw_date)

    found: dict[str, CurrencyRate] = {}
    for valute in root.findall("Valute"):
        char_code_el = valute.find("CharCode")
        nominal_el = valute.find("Nominal")
        value_el = valute.find("Value")
        if char_code_el is None or nominal_el is None or value_el is None:
            continue
        char_code = (char_code_el.text or "").strip().upper()
        if char_code not in REQUIRED_CURRENCIES:
            continue

        try:
            nominal = int((nominal_el.text or "").strip())
        except ValueError as exc:
            raise CbrValidationError(f"Invalid nominal for {char_code}") from exc
        try:
            rate_str = (value_el.text or "").strip().replace(",", ".")
            rate = float(rate_str)
        except ValueError as exc:
            raise CbrValidationError(f"Invalid rate value for {char_code}") from exc

        if nominal <= 0:
            raise CbrValidationError(f"Non-positive nominal for {char_code}: {nominal}")
        if rate <= 0:
            raise CbrValidationError(f"Non-positive rate for {char_code}: {rate}")

        found[char_code] = CurrencyRate(
            currency=char_code, nominal=nominal, rate=rate, rate_date=rate_date
        )

    missing = REQUIRED_CURRENCIES - found.keys()
    if missing:
        raise CbrValidationError(f"CBR response missing required currencies: {sorted(missing)}")

    return [found[c] for c in sorted(REQUIRED_CURRENCIES)]


def fetch_cbr_rates(
    endpoint: str = DEFAULT_CBR_ENDPOINT,
    on_date: date | None = None,
    max_retries: int = MAX_RETRIES,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> list[CurrencyRate]:
    """Fetch and validate USD/EUR/CNY rates from CBR with bounded retry + backoff.

    Raises `CbrHttpError` after `max_retries` failed attempts, and
    `CbrValidationError` immediately on a structurally invalid response
    (no retry on validation failures -- retrying won't fix bad data).
    """
    params = {}
    if on_date is not None:
        params["date_req"] = on_date.strftime("%d/%m/%Y")

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(endpoint, params=params, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "CBR request failed (attempt %s/%s): %s", attempt, max_retries, exc
            )
        else:
            if 500 <= response.status_code < 600:
                last_error = CbrHttpError(f"CBR server error: HTTP {response.status_code}")
                logger.warning(
                    "CBR server error (attempt %s/%s): HTTP %s",
                    attempt,
                    max_retries,
                    response.status_code,
                )
            elif 400 <= response.status_code < 500:
                # Client errors are not retried -- the request itself is wrong.
                raise CbrHttpError(f"CBR client error: HTTP {response.status_code}")
            else:
                response.encoding = "windows-1251"
                return parse_cbr_xml(response.content)

        if attempt < max_retries:
            backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            time.sleep(backoff)

    raise CbrHttpError(f"CBR endpoint unreachable after {max_retries} attempts") from last_error
