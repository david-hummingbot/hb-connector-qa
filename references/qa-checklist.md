# Hummingbot Connector QA Checklist

This checklist defines the mandatory tests for validating a new Hummingbot connector. Use it to ensure consistent quality across all PRs.

## 1. Environment & Connection
- [ ] **Check-out PR**: Verify the branch can be checked out and built without errors.
- [ ] **Connector Setup**: Run `setup_connector` and ensure all required credentials (API keys, secrets, etc.) are correctly identified.
- [ ] **Ping/Connect**: Verify the bot can successfully connect to the exchange API.

## 2. Market Data (Spot & Perp)
- [ ] **Latest Prices**: Run `get_market_data(data_type="prices")` for multiple pairs.
- [ ] **Order Book**: Fetch a snapshot using `get_market_data(data_type="order_book")`. Verify depth and spreads.
- [ ] **Candles**: Fetch OHLCV data using `get_market_data(data_type="candles")`.

## 3. Account & Balances
- [ ] **Token Balances**: Run `get_portfolio_overview(include_balances=True)`. Compare with exchange UI.
- [ ] **Permissions**: Verify the API key has the necessary permissions (Trade, View, etc.).

## 4. Trading (Execution)
- [ ] **Limit Buy/Sell**: Place small limit orders using `order_executor`.
- [ ] **Market Buy/Sell**: Execute market orders and verify immediate fill.
- [ ] **Cancel Orders**: Place a limit order and immediately cancel it using `action="stop"`.
- [ ] **Order Tracking**: Use `search_history(data_type="orders")` to verify order status (FILLED, CANCELED).

## 5. Perpetual Specifics (if applicable)
- [ ] **Position Mode**: Test setting 'HEDGE' vs 'ONE-WAY' modes.
- [ ] **Leverage**: Verify leverage can be set and updated for a pair.
- [ ] **Funding Rates**: Run `get_market_data(data_type="funding_rate")`.
- [ ] **Open Positions**: Verify open positions appear in `get_portfolio_overview(include_perp_positions=True)`.

## 6. DEX/CLMM Specifics (if applicable)
- [ ] **Pool Discovery**: Use `explore_dex_pools(action="list_pools")` to find active pools.
- [ ] **LP Provisioning**: Test opening a position using `lp_executor`.
- [ ] **Fee Collection**: Verify fees are correctly tracked in the portfolio view.
- [ ] **Swap/Quote**: Use `manage_gateway_swaps(action="quote")` to verify price routing.
