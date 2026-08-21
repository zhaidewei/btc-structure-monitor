# P1 / SMA35 / SMA300 Operational Contract

The production signal is intentionally conventional and auditable:

```text
At 00:17 UTC each day:
  ignore the still-open UTC candle
  SMA35  = mean of the latest 35 completed UTC daily closes
  SMA300 = mean of the latest 300 completed UTC daily closes

  SMA35 > SMA300 -> BTC
  SMA35 < SMA300 -> CASH
```

P1 means daily evaluation, not daily trading. The monitor changes state only when the two averages cross.

The dashboard signal is deterministic and cannot execute trades.

The monitor uses direct Coinbase BTC-EUR completed UTC daily candles and checks the latest completed close against OKX BTC-EUR. It does not derive the production signal by converting a USD or stablecoin series. A date mismatch or source divergence above the configured threshold fails data health closed.
