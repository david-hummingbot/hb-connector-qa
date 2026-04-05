#!/usr/bin/env python3
"""
QA checklist §3 — Account & Balances.
Live: POST /portfolio/state, GET /connectors/{name}/config-map
(hummingbot-api routers/portfolio.py, routers/connectors.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import HummingbotApiClient, cfg, fmt_err, log_result, require_connector_env  # noqa: E402
from _common import run_main  # noqa: E402

TESTS = [
    {
        "id": "token_balances",
        "name": "Token Balances",
        "mcp_tool": "POST /portfolio/state",
        "params": {
            "account_names": ["{HB_ACCOUNT}"],
            "connector_names": ["{HB_CONNECTOR}"],
            "skip_gateway": False,
            "refresh": True,
        },
        "notes": "Compare with exchange UI after refresh.",
    },
    {
        "id": "api_permissions",
        "name": "Permissions / credential schema",
        "mcp_tool": "GET /connectors/{connector}/config-map",
        "params": None,
        "notes": "Lists required credential fields (and types) for the connector.",
    },
]


def run_live(client: HummingbotApiClient, env: dict[str, str]) -> int:
    connector, _pair = require_connector_env(env)
    account = cfg(env, "HB_ACCOUNT")
    failures = 0

    st, data = client.post(
        "/portfolio/state",
        {
            "account_names": [account],
            "connector_names": [connector],
            "skip_gateway": False,
            "refresh": True,
        },
    )
    ok = st == 200 and isinstance(data, dict) and account in data and connector in data[account]
    log_result("Token Balances (portfolio/state)", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    st, data = client.request("GET", f"/connectors/{connector}/config-map")
    ok = st == 200 and isinstance(data, dict) and len(data) > 0
    log_result("Connector config-map (credential fields)", ok, "" if ok else f"{st} {fmt_err(data)}")
    failures += 0 if ok else 1

    return 1 if failures else 0


if __name__ == "__main__":
    run_main(TESTS, run_live=run_live)
