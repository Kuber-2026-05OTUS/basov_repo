from datetime import date

import pytest

from src.cbr_client import CbrValidationError, parse_cbr_xml

VALID_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="17.09.2026" name="Foreign Currency Market">
<Valute ID="R01235"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal><Name>Доллар США</Name><Value>92,5000</Value></Valute>
<Valute ID="R01239"><NumCode>978</NumCode><CharCode>EUR</CharCode><Nominal>1</Nominal><Name>Евро</Name><Value>100,1200</Value></Valute>
<Valute ID="R01375"><NumCode>156</NumCode><CharCode>CNY</CharCode><Nominal>1</Nominal><Name>Китайский юань</Name><Value>12,7500</Value></Valute>
</ValCurs>"""


def test_parse_cbr_xml_returns_required_currencies() -> None:
    rates = parse_cbr_xml(VALID_XML.encode("windows-1251"))
    codes = {r.currency for r in rates}
    assert codes == {"USD", "EUR", "CNY"}


def test_parse_cbr_xml_parses_date_and_values() -> None:
    rates = {r.currency: r for r in parse_cbr_xml(VALID_XML.encode("windows-1251"))}
    assert rates["USD"].rate_date == date(2026, 9, 17)
    assert rates["USD"].rate == pytest.approx(92.5)
    assert rates["EUR"].rate == pytest.approx(100.12)
    assert rates["CNY"].nominal == 1


def test_parse_cbr_xml_rejects_missing_currency() -> None:
    xml = VALID_XML.replace(
        '<Valute ID="R01375"><NumCode>156</NumCode><CharCode>CNY</CharCode>'
        "<Nominal>1</Nominal><Name>Китайский юань</Name><Value>12,7500</Value></Valute>",
        "",
    )
    with pytest.raises(CbrValidationError, match="missing required currencies"):
        parse_cbr_xml(xml.encode("windows-1251"))


def test_parse_cbr_xml_rejects_malformed_xml() -> None:
    with pytest.raises(CbrValidationError, match="Malformed"):
        parse_cbr_xml(b"<not><valid")


def test_parse_cbr_xml_rejects_missing_date() -> None:
    xml = VALID_XML.replace('Date="17.09.2026" ', "")
    with pytest.raises(CbrValidationError, match="missing Date"):
        parse_cbr_xml(xml.encode("windows-1251"))


def test_parse_cbr_xml_rejects_non_positive_rate() -> None:
    xml = VALID_XML.replace("<Value>92,5000</Value>", "<Value>0</Value>")
    with pytest.raises(CbrValidationError, match="Non-positive rate"):
        parse_cbr_xml(xml.encode("windows-1251"))


def test_parse_cbr_xml_rejects_non_positive_nominal() -> None:
    xml = VALID_XML.replace(
        '<CharCode>USD</CharCode><Nominal>1</Nominal>',
        '<CharCode>USD</CharCode><Nominal>0</Nominal>',
    )
    with pytest.raises(CbrValidationError, match="Non-positive nominal"):
        parse_cbr_xml(xml.encode("windows-1251"))
