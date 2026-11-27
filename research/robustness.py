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
from strategies import trend_filter
from strategies.selector import build_signal

HISTORY_START = "2004-01-01"
PERIODS = {"2006-2014": ("2006-01-01", "2014-12-31"), "2015-now": ("2015-01-01", None)}
# Index ETFs first: they cut the "I picked winners" problem of single stocks.
ASSET_ETFS = ["SPY", "QQQ", "^NSEI", "EFA", "TLT", "GLD"]  # diversified asset classes
DEFAULT_UNIVERSE = ASSET_ETFS + config.TICKERS

VARIANTS = {
    "gated long-only": lambda p: build_signal(p, allow_short=False),
    "gated long+short": lambda p: build_signal(p, allow_short=True),
    "close > 200d SMA": lambda p: p.assign(
        signal=(p["close"] > p["close"].rolling(200).mean()).astype(float)),
    "trend 50/100/200": lambda p: build_signal(p, strategies=[trend_filter]),
    "trend 50/100/200 + 10% vol": lambda p: build_signal(
        p, strategies=[trend_filter], params={"trend_filter": {"target_vol": 0.10}}),
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
        "exposure": res["position"].abs().mean(),
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

    rows, streams = [], {}
    for vname, builder in VARIANTS.items():
        for sname, (fee, fill) in SETTINGS.items():
            for pname, (start, end) in PERIODS.items():
                for t, prices in data.items():
                    res = run(prices, builder, start, end, fee, fill)
                    rows.append({"variant": vname, "setting": sname, "period": pname,
                                 "ticker": t, **row(res)})
                    if sname == "next-open, 10bps":
                        streams[(vname, pname, t)] = (res["strategy_return"], res["return"])
    table = pd.DataFrame(rows)

    pd.set_option("display.width", 200)
    print("\nAVERAGE ACROSS TICKERS (annual/max_dd/exposure are fractions)")
    avg = table.groupby(["variant", "setting", "period"], sort=False).mean(numeric_only=True)
    print(avg.round(3).to_string())

    print("\nHOW OFTEN DOES THE STRATEGY BEAT BUY & HOLD ON SHARPE? (next-open, 10bps)")
    sub = table[table["setting"] == "next-open, 10bps"].copy()
    sub["beats"] = sub["sharpe"] > sub["bh_sharpe"]
    print(sub.groupby(["variant", "period"], sort=False)["beats"].agg(["sum", "count"]).to_string())

    print("\nDIVERSIFIED PORTFOLIOS: equal weight, daily rebalanced (next-open, 10bps)")
    groups = {"asset-class ETFs": [t for t in ASSET_ETFS if t in data], "all tickers": list(data)}
    port = []
    for vname in VARIANTS:
        for pname in PERIODS:
            for gname, members in groups.items():
                cols = [streams[(vname, pname, t)] for t in members if (vname, pname, t) in streams]
                if not cols:
                    continue
                strat = pd.concat([c[0] for c in cols], axis=1).mean(axis=1).fillna(0)
                bh = pd.concat([c[1] for c in cols], axis=1).mean(axis=1).fillna(0)
                for label, r in (("strategy", strat), ("buy&hold", bh)):
                    eq = (1 + r).cumprod()
                    port.append({"variant": vname, "period": pname, "group": gname, "what": label,
                                 "annual": eq.iloc[-1] ** (252 / len(eq)) - 1,
                                 "sharpe": sharpe_ratio(r), "max_dd": max_drawdown(eq)})
    print(pd.DataFrame(port).round(3).to_string(index=False))

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
