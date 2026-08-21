# BTC Structure Monitor

A read-only monitor for the deterministic P1 / SMA35 / SMA300 BTC regime strategy. GitHub Actions refreshes public market data and publishes a static operational dashboard.

```text
market data -> deterministic SMA signal -> status.json
status + price history -> static dashboard -> GitHub Pages
```

The repository contains no exchange trading integration.

## What it monitors

- Daily BTC/CASH state from completed UTC SMA35 and SMA300 values.
- Distance to crossover, crossover frequency, and rapid reversals.
- Primary-versus-validation market-data divergence.

## Local run

Python 3.10 or newer is recommended. The monitor itself uses only the standard library.

```bash
python -m btc_monitor
python -m http.server 8000 -d site
```

Open `http://localhost:8000`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## GitHub deployment

The workflow runs at 00:17 and 01:17 UTC, persists generated JSON, and deploys `site/` with GitHub Pages. The second run acts as a retry.

Required GitHub configuration:

1. Enable Pages with GitHub Actions as the source.
2. Optionally add `LARK_WEBHOOK_URL` or Telegram secrets for signal-change notifications.
3. Run the `BTC structure monitor` workflow manually once.

See [deployment details](docs/deployment.md) and the exact [strategy contract](docs/strategy.md).

## Safety boundaries

- No exchange API key, wallet key, balance, address, or portfolio amount is needed.
- Market-data divergence fails visibly instead of silently changing sources.
