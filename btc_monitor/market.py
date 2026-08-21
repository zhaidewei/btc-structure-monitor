from __future__ import annotations

import csv
import datetime as dt
import io
import json
import urllib.parse
import urllib.request
import zipfile
from bisect import bisect_right
from dataclasses import asdict, dataclass
from typing import Iterable


UA = "btc-structure-monitor/0.1"


@dataclass(frozen=True)
class PricePoint:
    date: dt.date
    open_eur: float
    close_eur: float


def _request(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_uniswap_candles(pair_id: int) -> list[tuple[dt.date, float, float]]:
    url = "https://tradingstrategy.ai/api/candles-jsonl?" + urllib.parse.urlencode(
        {"pair_ids": str(pair_id), "time_bucket": "1d"}
    )
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    rows: list[tuple[dt.date, float, float]] = []
    with urllib.request.urlopen(request, timeout=90) as response:
        for raw in response:
            if not raw.strip():
                continue
            item = json.loads(raw)
            day = dt.datetime.fromtimestamp(item["ts"], dt.timezone.utc).date()
            rows.append((day, float(item["o"]), float(item["c"])))
    rows.sort(key=lambda row: row[0])
    return rows


def fetch_ecb_eur_usd() -> dict[dt.date, float]:
    raw = _request("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip")
    archive = zipfile.ZipFile(io.BytesIO(raw))
    text = archive.read(archive.namelist()[0]).decode("utf-8-sig")
    result: dict[dt.date, float] = {}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("USD") in (None, "", "N/A"):
            continue
        result[dt.date.fromisoformat(row["Date"])] = float(row["USD"])
    return result


def convert_to_eur(
    candles: Iterable[tuple[dt.date, float, float]], fx: dict[dt.date, float]
) -> list[PricePoint]:
    fx_dates = sorted(fx)
    points: list[PricePoint] = []
    for day, open_usd, close_usd in candles:
        index = bisect_right(fx_dates, day) - 1
        if index < 0:
            continue
        usd_per_eur = fx[fx_dates[index]]
        points.append(PricePoint(day, open_usd / usd_per_eur, close_usd / usd_per_eur))
    return points


def fetch_okx_last_confirmed_close(instrument: str) -> tuple[dt.date, float]:
    params = urllib.parse.urlencode({"instId": instrument, "bar": "1Dutc", "limit": "100"})
    payload = json.loads(_request(f"https://www.okx.com/api/v5/market/history-candles?{params}"))
    confirmed = [row for row in payload.get("data", []) if row[8] == "1"]
    if not confirmed:
        raise RuntimeError(f"OKX returned no confirmed candles for {instrument}")
    row = max(confirmed, key=lambda value: int(value[0]))
    day = dt.datetime.fromtimestamp(int(row[0]) / 1000, dt.timezone.utc).date()
    return day, float(row[4])


def latest_complete_points(points: list[PricePoint], now: dt.datetime | None = None) -> list[PricePoint]:
    current = now or dt.datetime.now(dt.timezone.utc)
    return [point for point in points if point.date < current.date()]


def serialise_points(points: Iterable[PricePoint]) -> list[dict[str, object]]:
    return [{**asdict(point), "date": point.date.isoformat()} for point in points]
