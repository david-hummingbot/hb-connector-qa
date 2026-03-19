# Hummingbot Connector QA Skill

This is an AI agent skill designed to automate the Quality Assurance (QA) process for new [Hummingbot](https://github.com/hummingbot/hummingbot) exchange connectors. 

It provides a standardized, repeatable workflow for testing exchange integrations (CEX Spot/Perpetual, DEX/CLMM) directly from a GitHub Pull Request.

## Features
- Automatically builds and tests the Hummingbot PR source code and Docker setups.
- Deploys the Hummingbot API server (`hummingbot-api`) in an isolated environment.
- Validates connection, market data extraction, portfolio balances, and order execution capabilities.
- Reports issues responsibly and stops test progression upon encountering critical failures without attempting arbitrary code changes.
- Generates a QA summary report ready to be posted back to the GitHub PR.

## Repository Structure
- `SKILL.md`: The main agent instruction file that drives the QA workflow.
- `references/`: 
  - `pr-setup.md`: Setup instructions for downloading and building the branch.
  - `hummingbot-api-setup.md`: Required background setup for the API server.
  - `qa-checklist.md`: The cross-referencing checklist for rigorous test validation.
- `scripts/`: 
  - `generate_qa_report.cjs`: A script to compile the final JSON test results into clean Markdown.

## Installation & Usage
To use this skill locally with your AI agent (like Antigravity / Gemini CLI):

1. Clone or copy this repository into your local workspace's skills directory (e.g., `~/.agents/skills/hummingbot-connector-qa`).
2. Give the agent a prompt with the PR link, for example:
   > "QA this PR for the new Hyperliquid connector: https://github.com/hummingbot/hummingbot/pull/123"
