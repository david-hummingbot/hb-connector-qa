# Hummingbot Connector QA Checklist

This checklist defines the mandatory tests for validating a new Hummingbot connector. Use it to ensure consistent quality across all PRs.

**Live HTTP tests** hit a running [hummingbot-api](https://github.com/hummingbot/hummingbot-api) instance. Paths and JSON bodies match that repo’s `routers/` and `models/` (use your local clone as the source of truth). Configure `.env` from [`.env.example`](../.env.example), then run `python3 scripts/checklist/<script>.py --run`. Use `--emit-json`, `--list`, or `--emit-md` for checklist text only (no network).

## 1. Environment & Connection
- [ ] **Check-out PR**: Verify the branch can be checked out and built without errors.
- [ ] **Connector Setup**: Run `setup_connector` and ensure all required credentials (API keys, secrets, etc.) are correctly identified.
- [ ] **Ping/Connect**: Verify the bot can successfully connect to the exchange API.

## 2. Market Data (Spot & Perp)

[`scripts/checklist/02_market_data.py`](../scripts/checklist/02_market_data.py) — `python3 scripts/checklist/02_market_data.py --run` (needs `HB_CONNECTOR`, `HB_TRADING_PAIR`).

## 3. Account & Balances

[`scripts/checklist/03_account_balances.py`](../scripts/checklist/03_account_balances.py) — `python3 scripts/checklist/03_account_balances.py --run`.

## 4. Trading (Execution)

[`scripts/checklist/04_trading_execution.py`](../scripts/checklist/04_trading_execution.py) — `python3 scripts/checklist/04_trading_execution.py --run` (set `HB_SKIP_MARKET=1` to avoid market orders).

## 5. Perpetual Specifics (if applicable)

[`scripts/checklist/05_perpetual_specifics.py`](../scripts/checklist/05_perpetual_specifics.py) — `python3 scripts/checklist/05_perpetual_specifics.py --run` (perp connector name only; optional `HB_LEVERAGE_TEST`, `HB_POSITION_MODE_WRITE_TEST`).

## 6. DEX/CLMM Specifics (if applicable)

[`scripts/checklist/06_dex_clmm_specifics.py`](../scripts/checklist/06_dex_clmm_specifics.py) — `python3 scripts/checklist/06_dex_clmm_specifics.py --run` (Gateway must be reachable for swap quote unless you accept a 503 skip).
