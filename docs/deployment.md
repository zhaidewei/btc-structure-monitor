# GitHub Actions and Pages Deployment

## Repository settings

1. Create the repository under the intended personal account.
2. Keep it private unless the user explicitly chooses public visibility.
3. In Settings -> Pages, select GitHub Actions as the source.
4. Confirm whether the resulting Pages site needs access control. Repository privacy does not by itself guarantee that every Pages plan publishes privately.

## Optional notification secrets

Configure only the integrations in use:

- `LARK_WEBHOOK_URL`: optional signal-change notification.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`: optional Telegram notification.

The monitor uses public read-only market endpoints. Do not add exchange trading credentials, wallet keys, balances, or addresses.

## Schedule

The workflow runs at 00:17 and 01:17 UTC. The first run is primary; the second is an idempotent retry.

Generated state under `site/data/` is committed by the workflow for simple durable history and auditability. The static `site/` directory is then deployed as a GitHub Pages artifact.
