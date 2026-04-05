#!/usr/bin/env python3
"""
QA checklist §5 — Perpetual-specific checks.
Live: GET/POST position-mode, POST leverage, POST /market-data/funding-info, POST /trading/positions
(hummingbot-api routers/trading.py, routers/market_data.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import HummingbotApiClient, cfg, fmt_err, log_result, require_connector_env  # noqa: E402
from _common import run_main  # noqa: E402

TESTS = [
    {
        "id": "position_mode_read",
        "name": "Position mode (read)",
        "mcp_tool": "GET /trading/{account}/{connector}/position-mode",
        "params": None,
        "applies_when": "perp_only",
    },
    {
        "id": "leverage",
        "name": "Leverage (write)",
        "mcp_tool": "POST /trading/.../leverage",
        "notes": "Skipped unless HB_LEVERAGE_TEST=1 (mutates account).",
        "applies_when": "perp_only",
    },
    {
        "id": "funding_rates",
        "name": "Funding info",
        "mcp_tool": "POST /market-data/funding-info",
        "params": {"connector_name": "{HB_CONNECTOR}", "trading_pair": "{HB_TRADING_PAIR}"},
        "applies_when": "perp_only",
    },
    {
        "id": "open_positions",
        "name": "Open positions",
        "mcp_tool": "POST /trading/positions",
        "params": {"limit": 50},
        "applies_when": "perp_only",
    },
]


def _looks_perpetual(connector: str) -> bool:
    n = connector.lower()
    return "perpetual" in n or n.endswith("_perp") or "_perp_" in n


def run_live(client: HummingbotApiClient, env: dict[str, str]) -> int:
    connector, pair = require_connector_env(env)
    if not _looks_perpetual(connector):
        print(
            "[SKIP] Perpetual suite — HB_CONNECTOR does not look like a perpetual connector "
            "(expected e.g. binance_perpetual)."
        )
        return 0

    account = cfg(env, "HB_ACCOUNT")
    failures = 0

    st, data = client.request("GET", f"/trading/{account}/{connector}/position-mode")
    ok = st == 200 and isinstance(data, dict)
    log_result("GET position-mode", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    if cfg(env, "HB_LEVERAGE_TEST") == "1":
        st, data = client.post(
            f"/trading/{account}/{connector}/leverage",
            {"trading_pair": pair, "leverage": 2},
        )
        ok = st == 200
        log_result("POST leverage (HB_LEVERAGE_TEST=1)", ok, "" if ok else f"{st} {fmt_err(data)}")
        failures += 0 if ok else 1
    else:
        log_result("POST leverage", True, "SKIPPED (set HB_LEVERAGE_TEST=1 to run)")

    st, data = client.post(
        "/market-data/funding-info",
        {"connector_name": connector, "trading_pair": pair},
    )
    ok = st == 200 and isinstance(data, dict)
    log_result("Funding info", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    st, data = client.post(
        "/trading/positions",
        {
            "limit": 50,
            "account_names": [account],
            "connector_names": [connector],
        },
    )
    ok = st == 200 and isinstance(data, dict) and "data" in data
    log_result("Open positions (POST /trading/positions)", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    if cfg(env, "HB_POSITION_MODE_WRITE_TEST") == "1":
        st, data = client.post(
            f"/trading/{account}/{connector}/position-mode",
            {"position_mode": "ONEWAY"},
        )
        ok = st == 200
        log_result("POST position-mode (HB_POSITION_MODE_WRITE_TEST=1)", ok, "" if ok else f"{st} {fmt_err(data)}")
        failures += 0 if ok else 1
    else:
        log_result("POST position-mode (write)", True, "SKIPPED (set HB_POSITION_MODE_WRITE_TEST=1)")

    return 1 if failures else 0


if __name__ == "__main__":
    run_main(TESTS, run_live=run_live)
