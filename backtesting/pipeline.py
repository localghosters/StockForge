"""Single entry point that turns a prices frame into everything the UI/CLI needs.

Pure pandas: no network, no database, no plotting. main.py and dashboard.py
can both call this so the numbers always agree.
"""
from backtesting.engine import run_backtest
from portfolio.metrics import summary
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
