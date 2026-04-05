#!/usr/bin/env python3
"""
QA checklist §2 — Market Data.
Live: POST /market-data/prices, /market-data/order-book, /market-data/candles
(hummingbot-api routers/market_data.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import (  # noqa: E402
    HummingbotApiClient,
    fmt_err,
    log_result,
    require_connector_env,
    trading_pairs_list,
)
from _common import run_main  # noqa: E402

TESTS = [
    {
        "id": "latest_prices",
        "name": "Latest Prices",
        "mcp_tool": "POST /market-data/prices",
        "params": {"connector_name": "{HB_CONNECTOR}", "trading_pairs": ["{HB_TRADING_PAIR}"]},
        "notes": "Requires HB_CONNECTOR and HB_TRADING_PAIR (or HB_TRADING_PAIRS).",
    },
    {
        "id": "order_book",
        "name": "Order Book",
        "mcp_tool": "POST /market-data/order-book",
        "params": {"connector_name": "{HB_CONNECTOR}", "trading_pair": "{HB_TRADING_PAIR}", "depth": 10},
        "notes": "Snapshot bids/asks; verify depth.",
    },
    {
        "id": "candles",
        "name": "Candles",
        "mcp_tool": "POST /market-data/candles",
        "params": {"connector_name": "{HB_CONNECTOR}", "trading_pair": "{HB_TRADING_PAIR}", "interval": "1m", "max_records": 50},
        "notes": "Live candle feed; may take up to MARKET_DATA_CANDLES_READY_TIMEOUT seconds.",
    },
]


def run_live(client: HummingbotApiClient, env: dict[str, str]) -> int:
    connector, pair = require_connector_env(env)
    pairs = trading_pairs_list(env, pair)
    failures = 0

    st, data = client.post(
        "/market-data/prices",
        {"connector_name": connector, "trading_pairs": pairs},
    )
    ok = st == 200 and isinstance(data, dict) and data.get("prices")
    if ok:
        for p in pairs:
            if p not in data["prices"]:
                ok = False
                break
    log_result("Latest Prices", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    st, data = client.post(
        "/market-data/order-book",
        {"connector_name": connector, "trading_pair": pair, "depth": 10},
    )
    ok = st == 200 and isinstance(data, dict) and data.get("bids") is not None and data.get("asks") is not None
    log_result("Order Book", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    st, data = client.post(
        "/market-data/candles",
        {
            "connector_name": connector,
            "trading_pair": pair,
            "interval": "1m",
            "max_records": 50,
        },
    )
    ok = st == 200 and isinstance(data, list) and len(data) > 0
    log_result("Candles", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    return 1 if failures else 0


if __name__ == "__main__":
    run_main(TESTS, run_live=run_live)
