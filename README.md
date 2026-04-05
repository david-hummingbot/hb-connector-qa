# Hummingbot Connector QA Skill

This is an AI agent skill designed to automate the Quality Assurance (QA) process for new [Hummingbot](https://github.com/hummingbot/hummingbot) exchange connectors.

It provides a standardized, repeatable workflow for testing exchange integrations (CEX Spot/Perpetual, DEX/CLMM) directly from a GitHub Pull Request.

**Source repository:** https://github.com/david-hummingbot/hb-connector-qa

## Features
- Checks for the `hummingbot-mcp` tool at startup and guides the user through installation if missing; falls back to manual `curl` commands if unavailable.
- Automatically builds and tests the Hummingbot PR source code and Docker setups.
- Deploys the Hummingbot API server (`hummingbot-api`) in an isolated environment.
- Validates connection, market data extraction, portfolio balances, and order execution capabilities.
- Reports issues responsibly and stops test progression upon encountering critical failures without attempting code changes.
- Generates a QA summary report, displays it to the user, and posts it back to the GitHub PR only upon confirmation.

## Requirements
- **hummingbot-mcp** (recommended): The skill uses the `hummingbot-mcp-docker` MCP server for all API interactions. Without it the skill falls back to raw `curl` commands.
- **Docker**: Required to run the hummingbot-mcp server and the hummingbot-api container.
- **Node.js**: Required to run the `generate_qa_report.cjs` report generation script.
- **Python 3.10+**: Required for `scripts/checklist/*.py` (`--run` uses stdlib `urllib` only).

## Repository Structure
- `SKILL.md`: The main agent instruction file that drives the QA workflow.
- `references/`:
  - `pr-setup.md`: Setup instructions for downloading and building the branch.
  - `hummingbot-api-setup.md`: Required background setup for the API server.
  - `qa-checklist.md`: The cross-referencing checklist for rigorous test validation.
- `scripts/`:
  - `collect_qa_env.sh`: Prompts for exchange credentials and writes `.env` (run after PR build succeeds).
  - `checklist/`: Python modules for QA checklist sections 2–6. They call **hummingbot-api** REST routes (same paths as your local [hummingbot-api](https://github.com/hummingbot/hummingbot-api) `routers/`). Use `python3 scripts/checklist/<script>.py --run` with `.env` from `.env.example`, or `--emit-json` / `--list` / `--emit-md` for spec-only output.
  - `generate_qa_report.cjs`: A script to compile the final JSON test results into clean Markdown.

## Installation & Usage
To use this skill locally with your AI agent (e.g. Antigravity / Gemini CLI):

1. Clone the repository into your agent's skills directory:
   ```bash
   git clone https://github.com/david-hummingbot/hb-connector-qa ~/.agents/skills/hummingbot-connector-qa
   ```
2. *(Optional but recommended)* Add `hummingbot-mcp` to your MCP server config (e.g. `~/.gemini/settings.json`):
   ```json
   "mcpServers": {
     "hummingbot-mcp-docker": {
       "command": "docker",
       "args": [
         "run", "--rm", "-i",
         "--network", "host",
         "-v", "hummingbot_mcp:/root/.hummingbot_mcp",
         "hummingbot/hummingbot-mcp:latest"
       ]
     }
   }
   ```
3. Give the agent a prompt with the PR link, for example:
   > "QA this PR for the new Hyperliquid connector: https://github.com/hummingbot/hummingbot/pull/123"

## Keeping the Skill Updated
When changes are pushed to the [source repository](https://github.com/david-hummingbot/hb-connector-qa), update your local copy using the command for your agent:

**Claude CLI** (`~/.claude/skills/hb-connector-qa`):
```bash
git -C ~/.claude/skills/hb-connector-qa pull
```

**Gemini CLI** (`~/.agents/skills/hummingbot-connector-qa`):
```bash
git -C ~/.agents/skills/hummingbot-connector-qa pull
```

To check your current version and recent changes:
```bash
# Claude
git -C ~/.claude/skills/hb-connector-qa log --oneline -10

# Gemini
git -C ~/.agents/skills/hummingbot-connector-qa log --oneline -10
```

> **Tip:** If you have local modifications, stash them before pulling:
> ```bash
> git -C <path> stash
> git -C <path> pull
> git -C <path> stash pop
> ```
