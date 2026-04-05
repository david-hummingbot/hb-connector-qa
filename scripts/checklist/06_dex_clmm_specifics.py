#!/usr/bin/env python3
"""
QA checklist §6 — DEX / CLMM (Gateway).
Live: GET /gateway/clmm/pools, POST /gateway/swap/quote, POST /gateway/clmm/positions_owned,
      POST /portfolio/state (gateway-inclusive)
(hummingbot-api routers/gateway_clmm.py, gateway_swap.py, portfolio.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import HummingbotApiClient, cfg, fmt_err, log_result  # noqa: E402
from _common import run_main  # noqa: E402

TESTS = [
    {
        "id": "pool_discovery",
        "name": "CLMM pool discovery",
        "mcp_tool": "GET /gateway/clmm/pools",
        "params": {"connector": "meteora", "limit": 20},
        "applies_when": "dex_only",
    },
    {
        "id": "lp_provisioning",
        "name": "CLMM positions owned",
        "mcp_tool": "POST /gateway/clmm/positions_owned",
        "notes": "Uses first pool from discovery or HB_CLMM_POOL_ADDRESS.",
        "applies_when": "dex_only",
    },
    {
        "id": "fee_collection",
        "name": "Portfolio incl. Gateway",
        "mcp_tool": "POST /portfolio/state",
        "notes": "refresh=true, skip_gateway=false to surface gateway-related balances.",
        "applies_when": "dex_only",
    },
    {
        "id": "swap_quote",
        "name": "Router swap quote",
        "mcp_tool": "POST /gateway/swap/quote",
        "params": {"connector": "jupiter", "network": "solana-mainnet-beta"},
        "applies_when": "dex_only",
    },
]


def run_live(client: HummingbotApiClient, env: dict[str, str]) -> int:
    failures = 0
    clmm_connector = cfg(env, "HB_DEX_CLMM_CONNECTOR")
    st, pools_data = client.request(
        "GET",
        "/gateway/clmm/pools",
        params=[
            ("connector", clmm_connector),
            ("limit", "10"),
        ],
    )
    pools_ok = st == 200 and isinstance(pools_data, dict) and pools_data.get("pools")
    log_result("CLMM pools list", bool(pools_ok), "" if pools_ok else f"{st} {fmt_err(pools_data)}")
    failures += 0 if pools_ok else 1

    pool_address = cfg(env, "HB_CLMM_POOL_ADDRESS").strip()
    network = cfg(env, "HB_CLMM_NETWORK").strip() or cfg(env, "HB_DEX_NETWORK")
    pools_list: list[Any] = pools_data.get("pools", []) if isinstance(pools_data, dict) else []
    if not pool_address and pools_list:
        first = pools_list[0]
        if isinstance(first, dict):
            pool_address = str(first.get("address", "")).strip()

    if pool_address and network:
        st, pos = client.post(
            "/gateway/clmm/positions_owned",
            {
                "connector": clmm_connector,
                "network": network,
                "pool_address": pool_address,
            },
        )
        pos_ok = st == 200 and isinstance(pos, list)
        log_result(
            "CLMM positions_owned",
            pos_ok,
            "" if pos_ok else f"{st} {fmt_err(pos)}",
        )
        if not pos_ok:
            failures += 1
    else:
        log_result(
            "CLMM positions_owned",
            True,
            "SKIPPED (need pool list + HB_CLMM_NETWORK or HB_DEX_NETWORK, or set HB_CLMM_POOL_ADDRESS)",
        )

    account = cfg(env, "HB_ACCOUNT")
    st, pstate = client.post(
        "/portfolio/state",
        {
            "account_names": [account],
            "skip_gateway": False,
            "refresh": True,
        },
    )
    pf_ok = st == 200 and isinstance(pstate, dict)
    log_result("Portfolio state (gateway-inclusive)", pf_ok, "" if pf_ok else f"{st} {fmt_err(pstate)}")
    failures += 0 if pf_ok else 1

    swap_body = {
        "connector": cfg(env, "HB_DEX_SWAP_CONNECTOR"),
        "network": cfg(env, "HB_DEX_NETWORK"),
        "trading_pair": cfg(env, "HB_DEX_PAIR"),
        "side": "BUY",
        "amount": 0.01,
        "slippage_pct": 1.0,
    }
    st, quote = client.post("/gateway/swap/quote", swap_body)
    if st == 503:
        log_result("Swap quote", True, "SKIPPED (Gateway unavailable — 503)")
    else:
        q_ok = st == 200 and isinstance(quote, dict)
        log_result("Swap quote", q_ok, "" if q_ok else f"{st} {fmt_err(quote)}")
        failures += 0 if q_ok else 1

    return 1 if failures else 0


if __name__ == "__main__":
    run_main(TESTS, run_live=run_live)
