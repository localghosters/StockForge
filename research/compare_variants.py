import pandas as pd
import config
from database.db import load_prices
from strategies.selector import build_signal, ALL_STRATEGIES
from backtesting.engine import run_backtest
from portfolio.metrics import total_return, sharpe_ratio, max_drawdown
from portfolio.diagnostics import trade_log

VARIANTS = [
    ("trend, regime filter", ["trend_breakout"], True),
    ("trend, always on", ["trend_breakout"], False),
    ("reversion, regime filter", ["mean_reversion"], True),
    ("reversion, always on", ["mean_reversion"], False),
    ("both, regime filter", ["trend_breakout", "mean_reversion"], True),
]


def run_variant(ticker, names, gated):
    prices = load_prices(ticker)
    chosen = [s for s in ALL_STRATEGIES if s.NAME in names]
    signals = build_signal(prices, chosen, gated).loc[config.EVAL_START:]
    return run_backtest(signals, config.INITIAL_CAPITAL, config.FEE_RATE)


rows = []
for ticker in config.TICKERS:
    for label, names, gated in VARIANTS:
        res = run_variant(ticker, names, gated)
        rows.append({
            "ticker": ticker,
            "variant": label,
            "return": total_return(res["equity"]),
            "sharpe": sharpe_ratio(res["strategy_return"].fillna(0)),
            "max_dd": max_drawdown(res["equity"]),
            "trades": len(trade_log(res)),
        })
    rows.append({
        "ticker": ticker,
        "variant": "buy and hold",
        "return": total_return(res["buy_hold"]),
        "sharpe": sharpe_ratio(res["return"].fillna(0)),
        "max_dd": max_drawdown(res["buy_hold"]),
        "trades": 1,
    })

print(pd.DataFrame(rows).round(3).to_string(index=False))