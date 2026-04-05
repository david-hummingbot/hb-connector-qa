"""Shared CLI, .env loading, and optional live-run wiring for QA checklist scripts (stdlib only)."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

SENSITIVE = frozenset({"API_KEY", "SECRET", "TRADING_PASSWORD"})


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def default_env_path() -> Path:
    p = os.environ.get("HB_QA_ENV")
    if p:
        return Path(p).expanduser().resolve()
    return skill_root() / ".env"


def load_env(path: Path | None = None) -> dict[str, str]:
    path = path or default_env_path()
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key:
            out[key] = val
    return out


def safe_substitute(text: str, env: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key in SENSITIVE:
            return m.group(0)
        return env.get(key, m.group(0))

    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, text)


def normalize_test(test: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    out = dict(test)
    for field in ("name", "notes"):
        if field in out and isinstance(out[field], str):
            out[field] = safe_substitute(out[field], env)
    return out


def prune_nones(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def emit_list(tests: list[dict[str, Any]], env: dict[str, str]) -> None:
    for raw in tests:
        t = normalize_test(raw, env)
        suffix = f" [{t['applies_when']}]" if t.get("applies_when") else ""
        print(f"- {t['name']}{suffix}")
        if t.get("notes"):
            print(f"    {t['notes']}")


def emit_md(tests: list[dict[str, Any]], env: dict[str, str]) -> None:
    for raw in tests:
        t = normalize_test(raw, env)
        parts = [f"- [ ] **{t['name']}**"]
        if t.get("mcp_tool"):
            parts.append(f" — `{t['mcp_tool']}`")
        line = "".join(parts)
        if t.get("params"):
            line += f" — params: `{json.dumps(t['params'], sort_keys=True)}`"
        if t.get("notes"):
            line += f" — {t['notes']}"
        if t.get("applies_when"):
            line += f" — *({t['applies_when']})*"
        print(line)


def emit_json(tests: list[dict[str, Any]], env: dict[str, str]) -> None:
    payload = [prune_nones(normalize_test(t, env)) for t in tests]
    print(json.dumps(payload, indent=2))


def run_main(
    tests: list[dict[str, Any]],
    run_live: Callable[..., int] | None = None,
) -> None:
    parser = argparse.ArgumentParser(
        description="QA checklist — spec output or --run against hummingbot-api (local repo routers).",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute live HTTP tests (requires API URL + HB_CONNECTOR / HB_TRADING_PAIR where applicable).",
    )
    parser.add_argument(
        "--emit-json",
        action="store_true",
        help="Print test definitions as JSON (no network).",
    )
    parser.add_argument(
        "--emit-md",
        action="store_true",
        help="Print markdown checklist lines (no network).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_human",
        help="Print human-readable bullet list (default if no other mode flag).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Override .env path (default: HB_QA_ENV or <skill>/.env).",
    )
    args = parser.parse_args()

    modes = (args.run, args.emit_json, args.emit_md, args.list_human)
    if sum(1 for m in modes if m) > 1:
        parser.error("use at most one of --run, --emit-json, --emit-md, --list")

    if args.run:
        if run_live is None:
            parser.error("internal error: --run not implemented for this script")
        import _client

        env = _client.effective_env(args.env_file)
        client = _client.make_client(env)
        code = run_live(client, env)
        raise SystemExit(code)

    env = load_env(args.env_file) if args.env_file else load_env()
    if args.emit_json:
        emit_json(tests, env)
    elif args.emit_md:
        emit_md(tests, env)
    else:
        emit_list(tests, env)
