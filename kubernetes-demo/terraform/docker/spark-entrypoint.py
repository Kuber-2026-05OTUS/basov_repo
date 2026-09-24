"""Run the repository Spark job, materializing CBR input when the Airflow task path is not shared."""
from __future__ import annotations

import datetime as dt
import pathlib
import sys
import xml.etree.ElementTree as ET

import requests


def _fetch_cbr(target: pathlib.Path, date: dt.date) -> None:
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    response = requests.get(url, params={"date_req": date.strftime("%d/%m/%Y")}, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    wanted = {"USD", "EUR", "CNY"}
    rows = []
    for item in root.findall("Valute"):
        code = item.findtext("CharCode")
        if code not in wanted:
            continue
        nominal = int(item.findtext("Nominal", "1"))
        rate = float(item.findtext("Value", "0").replace(",", "."))
        rows.append({"date": date.isoformat(), "currency": code, "nominal": nominal, "rate": rate, "source": "CBR"})
    if {row["currency"] for row in rows} != wanted:
        raise RuntimeError(f"CBR response does not contain USD/EUR/CNY for {date}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(__import__("json").dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    if "--input-path" not in sys.argv:
        raise SystemExit("--input-path is required")
    idx = sys.argv.index("--input-path")
    if idx + 1 >= len(sys.argv):
        raise SystemExit("--input-path requires a value")
    input_path = pathlib.Path(sys.argv[idx + 1])
    if not input_path.exists():
        # The existing DAG uses cbr_rates_YYYY-MM-DD.json in the path. Prefer
        # that date; otherwise use today's UTC date.
        name = input_path.name
        date = dt.date.today()
        marker = "cbr_rates_"
        if name.startswith(marker) and name.endswith(".json"):
            try:
                date = dt.date.fromisoformat(name[len(marker):-5])
            except ValueError:
                pass
        _fetch_cbr(input_path, date)
    from src.spark_job import main as spark_main
    return spark_main()


if __name__ == "__main__":
    raise SystemExit(main())
