"""Daily paper-trading signals for the trend-following basket.

    python -m live.signals_today                      # default basket
    python -m live.signals_today SPY QQQ GLD --vol-target 0.10

Run it once per day AFTER the market closes. It prints the target weights for
the next session and logs them to results/signals_log.csv so you can see what
changed. It places no orders. Paper trade it for months before real money.
Not financial advice; backtests do not guarantee future results.
"""
import argparse
from datetime import date, timedelta

import pandas as pd

import config
from data.fetch import download_prices
from strategies import trend_filter

DEFAULT_BASKET = ["SPY", "QQQ", "EFA", "TLT", "GLD"]
LOG = config.BASE_DIR / "results" / "signals_log.csv"


def target_weights(prices_by_ticker, vol_target=None):
    """Equal weight across assets; each asset's share scales with its trend votes."""
    n = len(prices_by_ticker)
    rows = []
    for t, df in prices_by_ticker.items():
        sig = trend_filter.signal(df, target_vol=vol_target).iloc[-1]
        rows.append({"ticker": t, "last_date": df.index[-1].date(), "close": df["close"].iloc[-1],
                     "sma200_gap": df["close"].iloc[-1] / df["close"].rolling(200).mean().iloc[-1] - 1,
                     "signal": sig, "weight": sig / n})
    out = pd.DataFrame(rows)
    out["weight"] = out["weight"].fillna(0.0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="*", default=DEFAULT_BASKET)
    ap.add_argument("--vol-target", type=float, default=None, help="e.g. 0.10 for 10%% annual vol")
    args = ap.parse_args()

    start = (date.today() - timedelta(days=700)).isoformat()
    data = {}
    for t in args.tickers:
        df = download_prices(t, start, None)
        if len(df) >= 250:
            data[t] = df
        else:
            print(f"skipping {t}: not enough data")
    out = target_weights(data, args.vol_target)

    if LOG.exists():
        prev = pd.read_csv(LOG).sort_values("run_date").groupby("ticker").tail(1).set_index("ticker")["weight"]
        out["prev_weight"] = out["ticker"].map(prev)
        out["changed"] = (out["weight"] - out["prev_weight"]).abs() > 1e-9
    LOG.parent.mkdir(exist_ok=True)
    stamp = out.assign(run_date=date.today().isoformat())
    stamp.to_csv(LOG, mode="a", header=not LOG.exists(), index=False)

    pd.set_option("display.width", 200)
    print(out.round(4).to_string(index=False))
    print(f"\nInvested: {out['weight'].sum():.1%}  |  Cash: {1 - out['weight'].sum():.1%}")


if __name__ == "__main__":
    main()



