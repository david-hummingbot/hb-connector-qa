---
name: hummingbot-connector-qa
description: Automate the QA process for new Hummingbot exchange connectors. Use when a user provides a GitHub PR link for a new connector or asks to test a specific exchange integration (CEX Spot/Perp, DEX/CLMM).
---

# Hummingbot Connector QA

This skill provides a standardized workflow for QA testers to validate new Hummingbot connectors. It ensures all mandatory tests (connection, balances, market data, and order execution) are performed and reported consistently.

## Workflow

To QA a new connector, follow these steps:

### 1. PR Setup & Environment
First, prepare the environment by running the PR setup workflows for both Source and Docker builds.
- Execute the [PR Setup Workflow](references/pr-setup.md). This is a Turbo Workflow. Substitute the PR ID from the user's prompt and run it to automatically perform the setup.
- **Source Build**: Must be completed and the client must start without errors.
- **Docker Build**: Must be completed and the container must start without issues.
- **Validation**: BOTH Source and Docker setups must pass. If one of them fails, mark the setup as incomplete and do NOT move on to the next test.

### 2. Hummingbot API Setup (Required)
Build the hummingbot library from the PR source and deploy it via hummingbot-api.
- Execute the [Hummingbot API Setup Workflow](references/hummingbot-api-setup.md). This is a Turbo Workflow. Run it to automatically perform the API setup.
- **Connection**: If `localhost` fails, try `host.docker.internal`.
- **CRITICAL RULE**: Throughout the duration of this skill, you MUST ONLY connect to the `hummingbot-api` server instance that you just created in this step. If there are other API servers connected or configured on the system, you must ignore them completely.
- If there are any issues or errors during this setup, notify the user immediately before proceeding.

### 3. Connection & Market Data
Ensure the connector can communicate with the exchange and retrieve data.
- Use `setup_connector` to configure credentials.
- Use `get_market_data` to verify:
  - `prices`: Latest ticker prices.
  - `order_book`: Snapshot depth and spreads.
  - `candles`: Historical OHLCV data.
  - `funding_rate`: (For Perps) Current funding rates.

### 4. Portfolio & Trading Execution
Test the core trading functionality using small amounts (Dust/Minimum order sizes).
- **Balances**: Use `get_portfolio_overview` to verify token balances.
- **Order Execution**: Use `order_executor` to test:
  - `LIMIT` Buy/Sell.
  - `MARKET` Buy/Sell.
  - `LIMIT_MAKER` (Post-only) orders.
- **Cancellation**: Verify orders can be stopped/cancelled immediately.
- **Position Management**: (For Perps/CLMM) Use `lp_executor` or `position_executor` to verify lifecycle tracking.

### 5. Generate QA Report
After testing, summarize the results using the bundled reporting script.
- Collect results in a JSON format: `[{"name": "Connect", "status": "PASS"}, {"name": "Limit Buy", "status": "FAIL", "notes": "Order rejected due to precision"}]`.
- Run the script: `node scripts/generate_qa_report.cjs '<json_results>'`.
- Post the generated Markdown report back to the GitHub PR.

## Bug & Error Handling Rule
**CRITICAL RULE**: If a bug or issue is found during any step of the QA process:
1. **NO CODE CHANGES**: Do not attempt to modify the codebase to fix the issue.
2. **LOG ERRORS**: Document the issue in a specific logfile (e.g., `qa_errors.log`). Your log MUST include:
   - Steps taken / steps to reproduce the issue.
   - The exact error messages and stack traces.
   - An explanation of the issue.
   - Suggested code changes (if any) to fix the issue.
3. **NOTIFY USER**: Inform the user about the issue immediately.
4. **CONTINUE IF POSSIBLE**: If it's still possible to proceed with other independent items in the checklist, continue testing. If the issue prevents further progress entirely, inform the user that the testing is halted and display the current overall test summary.

## Mandatory Checklist
Always cross-reference your tests with the [QA Checklist](references/qa-checklist.md) to ensure no connector-specific requirements are missed.

## Examples

**User:** "QA this PR for the new Hyperliquid connector: https://github.com/hummingbot/hummingbot/pull/123"
**Gemini CLI:** *Activates skill, reads PR setup, performs environment checks, and guides the user through the checklist.*

**User:** "Test the balance and limit order execution for the new Binance Spot connector."
**Gemini CLI:** *Uses `get_portfolio_overview` and `order_executor` to perform the requested tests and reports the outcome.*
