from __future__ import annotations

import datetime as dt
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


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


def fetch_coinbase_candles(
    product_id: str, start: dt.date, end: dt.date
) -> list[PricePoint]:
    if end < start:
        raise ValueError("end must not be earlier than start")
    rows_by_day: dict[dt.date, PricePoint] = {}
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + dt.timedelta(days=290), end)
        params = urllib.parse.urlencode(
            {
                "granularity": "86400",
                "start": f"{cursor.isoformat()}T00:00:00Z",
                "end": f"{chunk_end.isoformat()}T00:00:00Z",
            }
        )
        url = f"https://api.exchange.coinbase.com/products/{product_id}/candles?{params}"
        payload = json.loads(_request(url))
        if not isinstance(payload, list):
            raise RuntimeError(f"Coinbase returned an invalid response for {product_id}")
        for row in payload:
            if not isinstance(row, list) or len(row) < 5:
                continue
            day = dt.datetime.fromtimestamp(int(row[0]), dt.timezone.utc).date()
            if start <= day <= end:
                rows_by_day[day] = PricePoint(day, float(row[3]), float(row[4]))
        cursor = chunk_end + dt.timedelta(days=1)
    return [rows_by_day[day] for day in sorted(rows_by_day)]


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
