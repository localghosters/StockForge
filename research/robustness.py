"""Does the strategy hold up? Long history, many assets, honest fills, luck tests.

    python -m research.robustness                 # default universe
    python -m research.robustness AAPL SPY ^NSEI  # your own tickers

Needs network (downloads ~20 years of daily bars via yfinance). Nothing is
tuned here: every variant uses the parameters already in config.py.
"""
import sys

import pandas as pd

import config
from backtesting.engine import run_backtest
from data.fetch import download_prices
from portfolio.metrics import annual_return, max_drawdown, sharpe_ratio
from portfolio.robustness import random_timing_test, sharpe_ci
from strategies.selector import build_signal

HISTORY_START = "2004-01-01"
PERIODS = {"2006-2014": ("2006-01-01", "2014-12-31"), "2015-now": ("2015-01-01", None)}
# Index ETFs first: they cut the "I picked winners" problem of single stocks.
DEFAULT_UNIVERSE = ["SPY", "QQQ", "^NSEI"] + config.TICKERS

VARIANTS = {
    "gated long-only": lambda p: build_signal(p, allow_short=False),
    "gated long+short": lambda p: build_signal(p, allow_short=True),
    "close > 200d SMA": lambda p: p.assign(
        signal=(p["close"] > p["close"].rolling(200).mean()).astype(float)),
}
SETTINGS = {  # name -> (fee per unit traded, fill model)
    "close fill, 10bps": (0.001, "close"),
    "next-open, 10bps": (0.001, "next_open"),
    "next-open, 30bps": (0.003, "next_open"),
}


def run(prices, builder, start, end, fee, fill):
    sig = builder(prices).loc[start:end]
    return run_backtest(sig, config.INITIAL_CAPITAL, fee, config.SHORT_BORROW_RATE, fill)


def row(res):
    years = len(res) / 252
    return {
        "annual": annual_return(res["equity"]),
        "sharpe": sharpe_ratio(res["strategy_return"].fillna(0)),
        "max_dd": max_drawdown(res["equity"]),
        "invested": (res["position"] != 0).mean(),
        "turnover/yr": res["trade"].sum() / years,
        "bh_annual": annual_return(res["buy_hold"]),
        "bh_sharpe": sharpe_ratio(res["return"].fillna(0)),
        "bh_dd": max_drawdown(res["buy_hold"]),
    }


def main(tickers):
    data = {}
    for t in tickers:
        df = download_prices(t, HISTORY_START, None)
        if len(df) > 1000:
            data[t] = df
        else:
            print(f"skipping {t}: not enough data")

    rows = []
    for vname, builder in VARIANTS.items():
        for sname, (fee, fill) in SETTINGS.items():
            for pname, (start, end) in PERIODS.items():
                for t, prices in data.items():
                    rows.append({"variant": vname, "setting": sname, "period": pname,
                                 "ticker": t, **row(run(prices, builder, start, end, fee, fill))})
    table = pd.DataFrame(rows)

    pd.set_option("display.width", 200)
    print("\nAVERAGE ACROSS TICKERS (annual/max_dd/invested are fractions)")
    avg = table.groupby(["variant", "setting", "period"], sort=False).mean(numeric_only=True)
    print(avg.round(3).to_string())

    print("\nHOW OFTEN DOES THE STRATEGY BEAT BUY & HOLD ON SHARPE? (next-open, 10bps)")
    sub = table[table["setting"] == "next-open, 10bps"].copy()
    sub["beats"] = sub["sharpe"] > sub["bh_sharpe"]
    print(sub.groupby(["variant", "period"], sort=False)["beats"].agg(["sum", "count"]).to_string())

    print("\nLUCK TESTS: gated long-only, next-open, 10bps, full history")
    out = []
    for t, prices in data.items():
        res = run(prices, VARIANTS["gated long-only"], PERIODS["2006-2014"][0], None, 0.001, "next_open")
        lo, hi = sharpe_ci(res["strategy_return"])
        rt = random_timing_test(res, 0.001)
        out.append({"ticker": t, "sharpe": rt["actual_sharpe"], "ci_low": lo, "ci_high": hi,
                    "random_median": rt["median_random_sharpe"], "p_value": rt["p_value"]})
    print(pd.DataFrame(out).round(3).to_string(index=False))
    print("\nRead it like this: a CI that includes 0 means 'cannot tell from zero'. "
          "A p_value above ~0.1 means the timing is not clearly better than shifting "
          "the same positions to random dates.")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_UNIVERSE)
