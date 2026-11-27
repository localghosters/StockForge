# Paper trading guide

`live/signals_today.py` produces the trend-following portfolio's target weights for the next
session. It **places no orders** and has no broker connection. Use it to paper trade first:
follow the signals on paper (or in a spreadsheet), and only consider real money after you
have watched it behave for a meaningful stretch.

> Not financial advice. Backtests don't guarantee future results, and nothing here is a
> recommendation to buy or sell any security.

## Daily routine

1. **After the market closes** (and once your data source has the final bar), from the repo root:
   ```bash
   python -m live.signals_today --vol-target 0.10
   ```
   Optionally pass your own tickers: `python -m live.signals_today SPY QQQ GLD`.
2. Check `last_date` in the output. If it is not the most recent trading day, the data
   provider hasn't published it yet; run it again later.
3. Read the table:

   | Column | Meaning |
   |---|---|
   | `close` | Last close used |
   | `sma200_gap` | Close vs its 200-day average (negative = below) |
   | `signal` | Trend score 0–1: the share of the 50/100/200-day averages price is above, scaled down by the vol target if used |
   | `weight` | Share of the portfolio: `signal / number of assets`. Each asset is capped at `1/N`. |
   | `prev_weight`, `changed` | Weight on the previous logged run, and whether it moved |

   Weights sum to at most 100%; the remainder is cash. A mostly-cash portfolio is normal
   when most assets are in downtrends: that is the mechanism that limited drawdowns in the backtests.
4. Each run is appended to `results/signals_log.csv` (git-ignored).
5. Execute on paper at **the next session's open**. That matches the `next_open` fill
   model the backtests assume. Record the fill price you would have got.

## What to track

A simple sheet with one row per day is enough:

- date, the target weights, your paper-trade fills, portfolio value
- the same portfolio's value under plain buy & hold of the same assets (equal weight)
- running max drawdown of each

Compare them regularly. The expected outcome from the research is *smaller drawdowns and
a similar-or-lower return than buy & hold*, not a higher return. If paper results behave
very differently from the backtest (for example much larger drawdowns, or constant
whipsawing), find out why before going further.

## Practical points

- **Rebalancing:** the backtests rebalance daily. With the vol target, weights drift by tiny
  amounts each day. In practice you'd likely only trade when a weight changes meaningfully.
  That is a deviation from what was tested, so check it in paper trading rather than assuming it is equivalent.
- **Costs:** the backtests assume 10 bps per unit traded, and the results degrade at 30 bps.
  Real costs depend on your broker, the instrument, and (for non-US assets) local charges.
- **What you can actually buy:** `^NSEI` is an index, not a product. India-listed ETFs
  (for example NIFTYBEES.NS, GOLDBEES.NS) have shorter histories and different costs.
  Buying US-listed ETFs from India involves remittance and tax rules. Check these before assuming the basket is tradable.
- **Taxes:** a trend system trades several times a year, which can mean short-term gains.
  Check the current rules with a tax professional.
- **Cash:** the backtests pay 0% on cash. Real cash can earn a yield, which would improve
  results, but this has not been modelled yet.
- **Shorting:** the live script is long-only. Retail short selling in Indian cash equities
  is generally restricted, so don't add shorts without checking what your broker and the rules allow.

## When to stop and re-think

- The paper portfolio's drawdown is clearly worse than buy & hold's.
- Signals flip back and forth every few days (whipsaw) and costs would eat the returns.
- A change you make to the rules wasn't tested with `research.robustness`.
- You find yourself overriding signals by feel. If the rules aren't trusted, the system isn't usable.
