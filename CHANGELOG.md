# Changelog

All notable changes to StockForge are documented here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Web dashboard** (`dashboard.py`, Streamlit + Plotly): candlestick chart with buy/sell markers and regime shading, equity vs buy & hold, drawdown, diagnostics, trade/action logs, CSV export, strategy and fill-model selectors.
- **Parameter-sweep heatmap** tab and `sweep_grid()` for two-parameter grids (Sharpe, total return or max drawdown).
- **`backtesting/pipeline.py`:** `run_pipeline()` is the single path from prices to results; `main.py` and the dashboard both use it.
- **Next-open fill model** in the engine (`run_backtest(..., fill="next_open")`); the default stays `"close"`.
- **Trend filter strategy** (`strategies/trend_filter.py`): long-only 50/100/200-day vote with optional volatility targeting.
- **Robustness tooling** (`portfolio/robustness.py`, `research/robustness.py`): ~20-year multi-asset comparison, cost stress, bootstrap Sharpe CI, random-timing luck test, paired Sharpe-difference test, diversified-portfolio tables.
- **Live paper-trading signals** (`live/signals_today.py`), logging to `results/signals_log.csv`.
- **Tests** (`tests/test_pipeline.py`, `tests/test_robustness.py`) and a GitHub Actions workflow that runs them.
- **Documentation:** rewritten README, `documentation/USAGE.md`, `documentation/METHODOLOGY.md`, `documentation/PAPER_TRADING.md`, `documentation/ROADMAP.md`, PR template.
- `requirements-dev.txt` (adds pytest).

### Changed
- `main.py` now calls `run_pipeline()`; console output is unchanged.
- `requirements.txt` rewritten and commented.
- `CONTRIBUTING.md` updated with development setup and evidence expected for new strategies.

### Removed
- Unused dependencies `scipy`, `statsmodels` and `sqlalchemy` from `requirements.txt` (nothing imported them).

### Findings
- The original regime-gated strategy showed no edge on honest tests, and shorting lost money in every test. A diversified trend-filter portfolio works as drawdown control. Details in [documentation/METHODOLOGY.md](documentation/METHODOLOGY.md).
