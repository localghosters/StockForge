# Roadmap

These are ideas, not promises. Items marked ★ would most improve how far the results can be trusted.

## Testing quality
- ★ **Cash yield setting:** the engine currently pays 0% on cash, which understates low-exposure strategies and makes the buy & hold comparison tougher than reality.
- ★ **Walk-forward evaluation:** fixed rules scored on successive out-of-sample windows.
- ★ **Tune/check split in the dashboard sweep tab:** two heatmaps side by side so overfitting is visible, not just warned about.
- India-tradable universe test (e.g. NIFTYBEES.NS, GOLDBEES.NS) alongside the US ETF basket.
- Slippage/spread model beyond a flat fee.

## Features
- Portfolio view: combine tickers into one equity curve with equal or custom weights.
- Optional weight-change band for live signals, evaluated in the backtest first.
- Dashboard screenshot and short demo in the README.

## Engineering
- Lint and formatting checks in CI.
- Type hints on the public functions in `backtesting/` and `portfolio/`.
- Packaging (`pyproject.toml`) so StockForge can be installed with `pip`.
