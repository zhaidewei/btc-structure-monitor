from __future__ import annotations

import datetime as dt
from dataclasses import asdict
from typing import Any

from .config import ROOT, load_config
from .io import read_json, write_json
from .market import (
    convert_to_eur,
    fetch_ecb_eur_usd,
    fetch_okx_last_confirmed_close,
    fetch_uniswap_candles,
    latest_complete_points,
    serialise_points,
)
from .notify import notify
from .render import render_index
from .signals import build_snapshot


SITE = ROOT / "site"
DATA = SITE / "data"


def run_monitor() -> dict[str, Any]:
    config = load_config()
    strategy = config["strategy"]
    market = config["market"]
    now = dt.datetime.now(dt.timezone.utc)

    candles = fetch_uniswap_candles(int(market["primary_pair_id"]))
    points = latest_complete_points(convert_to_eur(candles, fetch_ecb_eur_usd()), now)
    snapshot, signal_history = build_snapshot(
        points,
        int(strategy["short_window"]),
        int(strategy["long_window"]),
        float(strategy["watch_band_pct"]),
    )

    validation_day, validation_price = fetch_okx_last_confirmed_close(market["validation_instrument"])
    primary_price = snapshot.last_price
    divergence = abs(primary_price / validation_price - 1.0) * 100.0
    source_ok = divergence <= float(market["max_source_divergence_pct"])
    previous = read_json(DATA / "status.json", {})

    status: dict[str, Any] = {
        "generated_at": now.isoformat(),
        "strategy": strategy,
        "signal": asdict(snapshot),
        "data_health": {
            "status": "ok" if source_ok else "divergent",
            "primary": market["primary_name"],
            "primary_as_of": snapshot.as_of,
            "validation": market["validation_instrument"],
            "validation_as_of": validation_day.isoformat(),
            "validation_price": validation_price,
            "divergence_pct": divergence,
        },
    }

    write_json(DATA / "status.json", status)
    chart_history = [
        {
            "date": row["date"].isoformat(),
            "price": round(float(row["price"]), 2),
            "short_sma": round(float(row["short_sma"]), 2),
            "long_sma": round(float(row["long_sma"]), 2),
            "signal": row["signal"],
            "crossover": row["crossover"],
        }
        for row in signal_history[-730:]
    ]
    write_json(DATA / "history.json", chart_history)
    render_index(SITE / "index.template.html", SITE / "index.html", "BTC Structure Monitor")

    old_signal = previous.get("signal", {}).get("signal")
    if old_signal and old_signal != snapshot.signal:
        delivered = notify(
            f"BTC strategy signal changed: {old_signal} -> {snapshot.signal}\n"
            f"SMA35/SMA300 gap: {snapshot.gap_pct:.2f}%\nAs of: {snapshot.as_of} UTC"
        )
        status["notification"] = {"channels": delivered, "reason": "signal_change"}
        write_json(DATA / "status.json", status)
    return status
