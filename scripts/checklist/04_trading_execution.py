#!/usr/bin/env python3
"""
QA checklist §4 — Trading execution.
Live: POST /trading/orders, cancel, /trading/orders/search; optional MARKET
(hummingbot-api routers/trading.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import HummingbotApiClient, cfg, fmt_err, log_result, require_connector_env  # noqa: E402
from _common import run_main  # noqa: E402

TESTS = [
    {
        "id": "limit_buy_sell",
        "name": "Limit order + cancel",
        "mcp_tool": "POST /trading/orders + POST .../cancel",
        "params": {"order_type": "LIMIT", "trade_type": "BUY"},
        "notes": "Places a LIMIT buy far below mid, then cancels (see HB_LIMIT_OFFSET_PCT).",
    },
    {
        "id": "market_buy_sell",
        "name": "Market order",
        "mcp_tool": "POST /trading/orders",
        "params": {"order_type": "MARKET"},
        "notes": "Skipped if HB_SKIP_MARKET=1 (real funds).",
    },
    {
        "id": "order_tracking",
        "name": "Order tracking",
        "mcp_tool": "POST /trading/orders/search",
        "params": {"limit": 50},
        "notes": "Historical/registry orders for account+connector+pair.",
    },
]


def _min_trade_amount(client: HummingbotApiClient, connector: str, pair: str, env: dict[str, str]) -> float:
    default = float(cfg(env, "HB_TEST_ORDER_AMOUNT") or "0.001")
    st, rules = client.request(
        "GET",
        f"/connectors/{connector}/trading-rules",
        params=[("trading_pairs", pair)],
    )
    if st != 200 or not isinstance(rules, dict):
        return default
    block: Any = rules.get(pair)
    if block is None and len(rules) == 1:
        block = next(iter(rules.values()))
    if not isinstance(block, dict):
        return default
    for key in ("min_order_size", "min_base_amount_increment"):
        v = block.get(key)
        if v is not None:
            try:
                return max(float(v), default)
            except (TypeError, ValueError):
                break
    return default


def run_live(client: HummingbotApiClient, env: dict[str, str]) -> int:
    connector, pair = require_connector_env(env)
    account = cfg(env, "HB_ACCOUNT")
    failures = 0
    offset_pct = float(cfg(env, "HB_LIMIT_OFFSET_PCT") or "10")

    st, px = client.post(
        "/market-data/prices",
        {"connector_name": connector, "trading_pairs": [pair]},
    )
    if st != 200 or not isinstance(px, dict) or not px.get("prices") or pair not in px["prices"]:
        log_result("Limit + cancel (price fetch)", False, f"{st} {fmt_err(px)}")
        return 1
    mid = float(px["prices"][pair])
    limit_price = mid * (1.0 - offset_pct / 100.0)
    amount = _min_trade_amount(client, connector, pair, env)

    st, placed = client.post(
        "/trading/orders",
        {
            "account_name": account,
            "connector_name": connector,
            "trading_pair": pair,
            "trade_type": "BUY",
            "amount": amount,
            "order_type": "LIMIT",
            "price": limit_price,
            "position_action": "OPEN",
        },
    )
    oid = placed.get("order_id") if isinstance(placed, dict) else None
    ok_place = st == 201 and oid
    log_result("LIMIT order placed", ok_place, "" if ok_place else f"{st} {fmt_err(placed)}")
    failures += 0 if ok_place else 1

    ok_cancel = False
    if oid:
        stc, cdata = client.request(
            "POST",
            f"/trading/{account}/{connector}/orders/{oid}/cancel",
        )
        ok_cancel = stc == 200
        log_result("Order cancel", ok_cancel, "" if ok_cancel else f"{stc} {fmt_err(cdata)}")
        failures += 0 if ok_cancel else 1

    if cfg(env, "HB_SKIP_MARKET") == "1":
        log_result("Market order", True, "SKIPPED (HB_SKIP_MARKET=1)")
    else:
        market_body = {
            "account_name": account,
            "connector_name": connector,
            "trading_pair": pair,
            "trade_type": "BUY",
            "amount": amount,
            "order_type": "MARKET",
            "position_action": "OPEN",
        }
        stm, mdata = client.post("/trading/orders", market_body)
        ok_m = stm == 201
        log_result("Market order", ok_m, "" if ok_m else f"{stm} {fmt_err(mdata)}")
        failures += 0 if ok_m else 1

    st, hist = client.post(
        "/trading/orders/search",
        {
            "limit": 50,
            "account_names": [account],
            "connector_names": [connector],
            "trading_pairs": [pair],
        },
    )
    ok_h = st == 200 and isinstance(hist, dict) and "data" in hist
    log_result("Order search (history)", ok_h, "" if ok_h else f"{st} {fmt_err(hist)}")
    failures += 0 if ok_h else 1

    return 1 if failures else 0


if __name__ == "__main__":
    run_main(TESTS, run_live=run_live)
