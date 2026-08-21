# Repository Contract

This public repository contains only deterministic technical monitoring.

- `btc_monitor/signals.py` is the source of truth for the SMA35/SMA300 BTC/CASH signal.
- Use UTC daily data and exclude incomplete UTC candles.
- Fail closed on stale or divergent market data. Never convert missing data into a healthy status.
- Never commit API keys, webhooks, wallet addresses, balances, or portfolio amounts.
- Dashboard output is static and read-only.
