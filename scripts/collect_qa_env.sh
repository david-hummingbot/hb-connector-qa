#!/usr/bin/env bash
# Interactive (or env-driven) credential collection for connector QA.
# Run from the skill root after PR build succeeds; writes .env for checklist scripts and MCP setup.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT="${HB_QA_ENV:-$SKILL_ROOT/.env}"

value_from_file() {
  local key="$1"
  [[ -f "$OUT" ]] || return 1
  local line
  line="$(grep -E "^${key}=" "$OUT" 2>/dev/null | tail -1)" || return 1
  [[ -n "$line" ]] || return 1
  printf '%s' "${line#*=}"
}

current_value() {
  local key="$1"
  local indirect="${!key-}"
  if [[ -n "$indirect" ]]; then
    printf '%s' "$indirect"
    return 0
  fi
  value_from_file "$key" || true
}

prompt_if_empty() {
  local key="$1" label="$2" secret="$3"
  local val
  val="$(current_value "$key")"
  if [[ -n "$val" ]]; then
    printf -v "$key" '%s' "$val"
    export "$key"
    return 0
  fi
  if [[ ! -t 0 ]]; then
    echo "Error: ${key} is required (non-interactive). Set it in the environment or in ${OUT}." >&2
    exit 1
  fi
  if [[ "$secret" == "1" ]]; then
    read -rsp "${label}: " val || true
    echo "" >&2
  else
    read -rp "${label}: " val || true
  fi
  printf -v "$key" '%s' "$val"
  export "$key"
}

preserve_other_lines() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  grep -v -E '^(API_KEY|SECRET|TRADING_PASSWORD)=' "$f" 2>/dev/null \
    | grep -v '^# Generated / updated by scripts/collect_qa_env' \
    | grep -v '^# Optional: set HB_QA_ENV' \
    | grep -v '^# --- preserved from existing file ---' || true
}

write_env() {
  local tmp
  tmp="$(mktemp)"
  {
    echo "# Generated / updated by scripts/collect_qa_env.sh — do not commit (.gitignored)"
    echo "# Optional: set HB_QA_ENV to use a different path."
    echo ""
    printf 'API_KEY=%s\n' "$(current_value API_KEY)"
    printf 'SECRET=%s\n' "$(current_value SECRET)"
    local tp
    tp="$(current_value TRADING_PASSWORD)"
    printf 'TRADING_PASSWORD=%s\n' "$tp"
    echo ""
    local rest
    rest="$(preserve_other_lines "$OUT")"
    if [[ -n "${rest//[$'\t\r\n ']/}" ]]; then
      echo "# --- preserved from existing file ---"
      printf '%s\n' "$rest"
    fi
  } >"$tmp"
  mv "$tmp" "$OUT"
  chmod 600 "$OUT" 2>/dev/null || true
}

main() {
  cd "$SKILL_ROOT"
  prompt_if_empty API_KEY "Exchange API key (API_KEY)" 0
  prompt_if_empty SECRET "Exchange API secret (SECRET)" 1
  if [[ -z "$(current_value TRADING_PASSWORD)" && -t 0 ]]; then
    read -rsp "Trading password if required by this exchange (optional, Enter to skip): " _tp || true
    echo "" >&2
    if [[ -n "${_tp}" ]]; then
      TRADING_PASSWORD="$_tp"
      export TRADING_PASSWORD
    fi
  fi
  if [[ -z "$(current_value API_KEY)" || -z "$(current_value SECRET)" ]]; then
    echo "Error: API_KEY and SECRET are required." >&2
    exit 1
  fi
  write_env
  echo "Wrote $OUT"
}

main "$@"
