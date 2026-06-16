# Domain Rules — Financial Time Series

When the data is stock / crypto / fund / market-factor data (price columns, OHLCV, tickers, factor panels), apply these specialized rules to avoid common pitfalls in financial data analysis.

## Target Variable Selection

**Raw price level (`close`)** is valid for *descriptive trend* statements only.

For driver ranking, factor analysis, or any predictive claim, default to **returns**:
- `log_return_1d` — single-period log returns
- `forward_return_5d` — forward 5-day returns
- `forward_return_20d` — forward 20-day returns  
- **Excess return vs benchmark** — when a benchmark exists (S&P 500, sector index, etc.)

**User-facing choice**: Present the target choice to the user as:
- **Price-level (descriptive)**: "What was the trend in stock price over this period?"
- **Returns (driver/predictive)**: "What factors drive future returns?" or "What predicts next-week performance?"

## Target-Derived Features

Anything computed from the target series must be tagged `target_derived` and **excluded from driver ranking**:

**Examples of target-derived features:**
- Momentum indicators (RSI, MACD)
- Moving averages of `Y` (MA50, MA200)
- Volatility of `Y` (rolling std, ATR)
- Technical patterns derived from `Y`

**Usage rules:**
- May appear as **technical-state descriptors** in reports
- **Never** as "drivers" or "predictors"
- If user asks "Does MA50 predict price?", explain the circularity and offer alternative (compare against independent factor)

## Stationarity & Autocorrelation

**Do not run plain correlation/regression on price levels.**

Price levels are non-stationary (have trends, drift). Correlations on non-stationary series produce spurious relationships.

**Options:**
1. **Use returns** (recommended) — log returns are approximately stationary
2. **Detrend** — difference the series or use residuals from trend model
3. **State the caveat** — if price-level analysis is required, explicitly note "non-stationarity not addressed" and downgrade claim to directional

**Test for stationarity:**
- Use Augmented Dickey-Fuller (ADF) test
- If p > 0.05, series is non-stationary → switch to returns or detrend

## Autocorrelation Handling

Financial time series often have strong autocorrelation.

**For regression/correlation:**
- Check residuals for autocorrelation (Durbin-Watson, Ljung-Box)
- If detected, use Newey-West standard errors or ARIMA framework
- Report effective sample size (accounts for correlation)

**For forecasting:**
- Consider ARIMA, GARCH, or state-space models
- Plain regression underestimates forecast uncertainty

## Investment Advice Prohibition

**Do not produce buy/sell/hold, position-sizing, or stop-loss recommendations** unless the user explicitly asks for trading-strategy analysis.

**Phrase results as:**
- Analytical scenarios: "If momentum exceeds threshold X, historical forward returns averaged Y%"
- Risk indicators: "Volatility in quintile 5 precedes drawdowns Z% of the time"
- Factor exposures: "This portfolio has 1.2x exposure to small-cap factor"

**Avoid:**
- "Buy when RSI < 30"
- "Take profit at +15%"
- "Allocate 60% to this stock"

**Exception:** If user explicitly asks "Design a trading strategy" or "What buy rules maximize Sharpe ratio?", treat as a strategy-design request and proceed, but include standard disclaimers about backtest overfitting and out-of-sample risk.

## Common Financial Anti-Patterns

Supplement the main anti-patterns.md with these financial-specific failures:

| 🚫 Anti-pattern | Why it fails | Do this instead |
|---|---|---|
| **Rank drivers against raw price** | Non-stationary → spurious correlations | Use returns or excess returns |
| **Call momentum indicator a "driver"** | Derived from target → mechanical correlation | Tag `target_derived`, exclude from ranking |
| **Ignore look-ahead bias** | Using future data in features → inflated backtest | Ensure all features use only past/concurrent data |
| **Backtest on same data** | Overfitting → poor out-of-sample | Hold out recent period; walk-forward validation |
| **Confuse correlation with edge** | Correlation ≠ tradable alpha after costs | Account for transaction costs, slippage, liquidity |

## Integration with Main Workflow

Financial time series analysis follows the same 7-stage workflow (intake → readiness → shaping → method-planner → execution → critic → report), with these domain-specific adaptations:

1. **Intake**: Identify OHLCV structure, ticker granularity, benchmark availability
2. **Readiness**: Check for sufficient history (≥2 years recommended), gaps (market holidays OK), survivorship bias
3. **Shaping**: Compute returns, align to common calendar, handle corporate actions (splits, dividends)
4. **Method-planner**: Default to returns-based methods; use cross-sectional when comparing securities
5. **Execution**: Apply Newey-West SEs if autocorrelation detected; use rolling windows for time-varying relationships
6. **Critic**: Flag target-derived features, check for look-ahead bias, verify stationarity
7. **Report**: State target choice (price vs returns), note non-stationarity caveats, avoid investment advice

## References

For detailed statistical methods on financial data:
- `method-registry.md` — Time series methods (ARIMA, Granger causality)
- `anti-patterns.md` — General statistical pitfalls
- `data-readiness.md` — Time coverage dimension

For recurring financial analysis patterns:
- `golden-templates.md` — Factor analysis template, momentum screening template
