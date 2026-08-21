from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .market import PricePoint


@dataclass(frozen=True)
class SignalSnapshot:
    as_of: str
    signal: str
    short_sma: float
    long_sma: float
    gap_pct: float
    last_price: float
    watch_band: bool
    crossover: str | None
    crossover_count_12m: int
    rapid_reversal_count_12m: int


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot calculate the mean of an empty series")
    return sum(values) / len(values)


def signal_series(points: list[PricePoint], short_window: int, long_window: int) -> list[dict[str, object]]:
    if short_window >= long_window:
        raise ValueError("short_window must be smaller than long_window")
    if len(points) < long_window:
        raise ValueError(f"need at least {long_window} complete daily points")
    closes = [point.close_eur for point in points]
    result: list[dict[str, object]] = []
    previous: str | None = None
    for index in range(long_window - 1, len(points)):
        short_sma = mean(closes[index - short_window + 1 : index + 1])
        long_sma = mean(closes[index - long_window + 1 : index + 1])
        signal = "BTC" if short_sma > long_sma else "CASH"
        crossover = None
        if previous is not None and signal != previous:
            crossover = "GOLDEN" if signal == "BTC" else "DEATH"
        result.append(
            {
                "date": points[index].date,
                "price": closes[index],
                "short_sma": short_sma,
                "long_sma": long_sma,
                "gap_pct": (short_sma / long_sma - 1.0) * 100.0,
                "signal": signal,
                "crossover": crossover,
            }
        )
        previous = signal
    return result


def build_snapshot(
    points: list[PricePoint], short_window: int, long_window: int, watch_band_pct: float
) -> tuple[SignalSnapshot, list[dict[str, object]]]:
    series = signal_series(points, short_window, long_window)
    current = series[-1]
    one_year_ago = current["date"] - dt.timedelta(days=365)
    recent_crosses = [row for row in series if row["date"] >= one_year_ago and row["crossover"]]
    rapid = 0
    prior_cross_date: dt.date | None = None
    for row in recent_crosses:
        if prior_cross_date and (row["date"] - prior_cross_date).days <= 60:
            rapid += 1
        prior_cross_date = row["date"]
    snapshot = SignalSnapshot(
        as_of=current["date"].isoformat(),
        signal=str(current["signal"]),
        short_sma=float(current["short_sma"]),
        long_sma=float(current["long_sma"]),
        gap_pct=float(current["gap_pct"]),
        last_price=float(current["price"]),
        watch_band=abs(float(current["gap_pct"])) <= watch_band_pct,
        crossover=current["crossover"] if isinstance(current["crossover"], str) else None,
        crossover_count_12m=len(recent_crosses),
        rapid_reversal_count_12m=rapid,
    )
    return snapshot, series
