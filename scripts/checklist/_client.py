"""
HTTP client for hummingbot-api REST endpoints.
Request/response shapes match the local hummingbot-api repo (routers/*.py, models/*.py).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from _common import load_env

# Defaults align with hummingbot-api config.py / docker .env (see local hummingbot-api repo).
_DEFAULTS: dict[str, str] = {
    "HUMMINGBOT_API_URL": "http://127.0.0.1:8000",
    "HUMMINGBOT_API_USER": "admin",
    "HUMMINGBOT_API_PASSWORD": "admin",
    "HB_ACCOUNT": "master_account",
    "HB_TEST_ORDER_AMOUNT": "0.001",
    "HB_LIMIT_OFFSET_PCT": "10",
    "HB_DEX_CLMM_CONNECTOR": "meteora",
    "HB_DEX_SWAP_CONNECTOR": "jupiter",
    "HB_DEX_NETWORK": "solana-mainnet-beta",
    "HB_DEX_PAIR": "SOL-USDC",
}

_MERGE_KEYS = frozenset(
    {
        "API_KEY",
        "SECRET",
        "TRADING_PASSWORD",
        "HUMMINGBOT_API_URL",
        "HUMMINGBOT_API_USER",
        "HUMMINGBOT_API_PASSWORD",
        "HB_ACCOUNT",
        "HB_CONNECTOR",
        "HB_TRADING_PAIR",
        "HB_TRADING_PAIRS",
        "HB_TEST_ORDER_AMOUNT",
        "HB_LIMIT_OFFSET_PCT",
        "HB_SKIP_MARKET",
        "HB_LEVERAGE_TEST",
        "HB_POSITION_MODE_WRITE_TEST",
        "HB_DEX_CLMM_CONNECTOR",
        "HB_DEX_SWAP_CONNECTOR",
        "HB_DEX_NETWORK",
        "HB_DEX_PAIR",
        "HB_CLMM_NETWORK",
        "HB_CLMM_POOL_ADDRESS",
    }
)


def effective_env(env_file: Path | None = None) -> dict[str, str]:
    """Merge `.env` with process environment (env vars override file)."""
    out = load_env(env_file)
    for k in _MERGE_KEYS:
        v = os.environ.get(k)
        if v is not None and v != "":
            out[k] = v
    return out


def cfg(env: dict[str, str], key: str) -> str:
    if env.get(key):
        return env[key]
    return _DEFAULTS.get(key, "")


def require_connector_env(env: dict[str, str]) -> tuple[str, str]:
    conn = cfg(env, "HB_CONNECTOR").strip()
    pair = cfg(env, "HB_TRADING_PAIR").strip()
    if not conn or not pair:
        raise SystemExit(
            "HB_CONNECTOR and HB_TRADING_PAIR must be set in `.env` (or environment) for --run. "
            "See `.env.example`."
        )
    return conn, pair


def trading_pairs_list(env: dict[str, str], pair: str) -> list[str]:
    raw = cfg(env, "HB_TRADING_PAIRS").strip()
    if not raw:
        return [pair]
    return [p.strip() for p in raw.split(",") if p.strip()]


class HummingbotApiClient:
    def __init__(self, base: str, user: str, password: str, timeout: float = 120.0):
        self.base = base.rstrip("/")
        self._auth = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        params: list[tuple[str, str]] | None = None,
    ) -> tuple[int, Any]:
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = None
        headers = {
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if body is not None:
            data = json.dumps(body, default=str).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode()
                status = resp.status
        except urllib.error.HTTPError as e:
            raw = e.read().decode() if e.fp else ""
            status = e.code
        except urllib.error.URLError as e:
            return 0, {"_error": str(e.reason)}
        try:
            parsed: Any = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            parsed = raw
        return status, parsed

    def get(
        self,
        path: str,
        params: list[tuple[str, str]] | None = None,
    ) -> tuple[int, Any]:
        return self.request("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        return self.request("POST", path, body=body)


def make_client(env: dict[str, str]) -> HummingbotApiClient:
    return HummingbotApiClient(
        cfg(env, "HUMMINGBOT_API_URL"),
        cfg(env, "HUMMINGBOT_API_USER"),
        cfg(env, "HUMMINGBOT_API_PASSWORD"),
    )


def fmt_err(parsed: Any) -> str:
    if isinstance(parsed, dict):
        if "_error" in parsed:
            return str(parsed["_error"])[:800]
        d = parsed.get("detail")
        if d is not None:
            return str(d)[:800]
        return str(parsed)[:800]
    return str(parsed)[:800]


def log_result(name: str, ok: bool, detail: str = "") -> None:
    tag = "PASS" if ok else "FAIL"
    line = f"[{tag}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
