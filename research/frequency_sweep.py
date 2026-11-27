import pandas as pd
import config
from database.db import load_prices
from strategies.selector import build_signal
from backtesting.engine import run_backtest
from portfolio.metrics import total_return, sharpe_ratio, max_drawdown
from portfolio.diagnostics import trade_log

PERIODS = {
    "tune": ("2019-06-01", "2022-12-31"),
    "check": ("2023-01-01", None),
}

VARIANTS = [
    {"name": "base", "kwargs": {}},
    {"name": "faster trend (10/5)",
     "kwargs": {"params": {"trend_breakout": {"entry_window": 10, "exit_window": 5}}}},
    {"name": "fastest trend (5/3)",
     "kwargs": {"params": {"trend_breakout": {"entry_window": 5, "exit_window": 3}}}},
    {"name": "looser reversion (RSI 20)",
     "kwargs": {"params": {"mean_reversion": {"rsi_entry": 20}}}},
    {"name": "also trade NEUTRAL days",
     "kwargs": {"extra_regimes": ["NEUTRAL"]}},
    {"name": "no CRISIS block", "vol_cap": 1.01, "kwargs": {}},
    {"name": "all of the above",
     "vol_cap": 1.01,
     "kwargs": {
         "params": {"trend_breakout": {"entry_window": 10, "exit_window": 5},
                    "mean_reversion": {"rsi_entry": 20}},
         "extra_regimes": ["NEUTRAL"]}},
]


def evaluate(variant, period, start, end):
    old_cap = config.VOL_CAP
    config.VOL_CAP = variant.get("vol_cap", old_cap)
    rows = []
    try:
        for ticker in config.TICKERS:
            prices = load_prices(ticker)
            sig = build_signal(prices, **variant["kwargs"]).loc[start:end]
            res = run_backtest(sig, config.INITIAL_CAPITAL, config.FEE_RATE)
            trades = trade_log(res)
            years = len(res) / 252
            rows.append({
                "variant": variant["name"],
                "period": period,
                "trades_per_year": len(trades) / years,
                "return": total_return(res["equity"]),
                "sharpe": sharpe_ratio(res["strategy_return"].fillna(0)),
                "max_dd": max_drawdown(res["equity"]),
                "expectancy": trades["return"].mean() if len(trades) else 0.0,
                "fees": (res["trade"] * config.FEE_RATE).sum(),
                "buy_hold": total_return(res["buy_hold"]),
            })
    finally:
        config.VOL_CAP = old_cap
    return rows


all_rows = []
for variant in VARIANTS:
    for period, (start, end) in PERIODS.items():
        all_rows += evaluate(variant, period, start, end)

table = pd.DataFrame(all_rows).groupby(["variant", "period"], sort=False).mean(numeric_only=True)
print("Average across all tickers (return, max_dd, fees and expectancy are fractions)")
print(table.round(3).to_string())
