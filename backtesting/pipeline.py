"""Single entry point that turns a prices frame into everything the UI/CLI needs.

Pure pandas: no network, no database, no plotting. main.py and dashboard.py
can both call this so the numbers always agree.
"""
import pandas as pd

import config
from backtesting.engine import run_backtest
from portfolio.metrics import max_drawdown, sharpe_ratio, summary, total_return
from portfolio.diagnostics import (
    trade_log, action_log, trade_stats, regime_table,
    strategy_contribution, yearly_table,
)
from strategies.selector import build_signal


def run_pipeline(prices, eval_start, capital, fee, borrow=0.0,
                 allow_short=False, strategy_params=None):
    signals = build_signal(prices, allow_short=allow_short, params=strategy_params)
    signals = signals.loc[eval_start:]
    result = run_backtest(signals, capital, fee, borrow)
    trades = trade_log(result)
    return {
        "result": result,
        "trades": trades,
        "actions": action_log(result),
        "summary": summary(result),
        "stats": trade_stats(trades, result, fee),
        "regimes": regime_table(result, fee),
        "contrib": strategy_contribution(result),
        "yearly": yearly_table(result),
    }


# ------------------------------------------------------------------ sweeps
# name -> ("strategy", strategy_name, kwarg) or ("config", CONFIG_ATTRIBUTE)
SWEEP_PARAMS = {
    "Breakout entry window": ("strategy", "trend_breakout", "entry_window"),
    "Breakout exit window": ("strategy", "trend_breakout", "exit_window"),
    "Mean-reversion RSI entry": ("strategy", "mean_reversion", "rsi_entry"),
    "Mean-reversion exit window": ("strategy", "mean_reversion", "exit_window"),
    "ADX trend threshold": ("config", "ADX_TREND"),
    "ADX range threshold": ("config", "ADX_RANGE"),
    "Volatility cap": ("config", "VOL_CAP"),
}

SWEEP_METRICS = {
    "Sharpe": lambda r: sharpe_ratio(r["strategy_return"].fillna(0)),
    "Total return": lambda r: total_return(r["equity"]),
    "Max drawdown": lambda r: max_drawdown(r["equity"]),
}


def _apply(name, value, params):
    kind = SWEEP_PARAMS[name]
    if kind[0] == "strategy":
        params.setdefault(kind[1], {})[kind[2]] = value
    else:
        setattr(config, kind[1], value)


def sweep_grid(prices, eval_start, capital, fee, borrow, allow_short,
               x_name, x_values, y_name, y_values, metric="Sharpe",
               base_params=None):
    """Run one backtest per (x, y) pair. Returns a frame: rows = y, columns = x."""
    saved = {kind[1]: getattr(config, kind[1])
             for kind in SWEEP_PARAMS.values() if kind[0] == "config"}
    grid = pd.DataFrame(index=list(y_values), columns=list(x_values), dtype=float)
    try:
        for y in y_values:
            for x in x_values:
                params = {k: dict(v) for k, v in (base_params or {}).items()}
                _apply(x_name, x, params)
                _apply(y_name, y, params)
                out = run_pipeline(prices, eval_start, capital, fee, borrow,
                                   allow_short, params)
                grid.loc[y, x] = SWEEP_METRICS[metric](out["result"])
    finally:
        for attr, value in saved.items():
            setattr(config, attr, value)
    grid.index.name, grid.columns.name = y_name, x_name
    return grid
