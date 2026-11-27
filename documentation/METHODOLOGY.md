# Methodology: evaluating strategies without fooling yourself

Most backtests that look good are wrong. This page explains how StockForge tries not to
be, the protocol to follow before trusting a result, and a log of what has been tried.

## Principles built into the code

| Risk | What StockForge does |
|---|---|
| **Lookahead bias** | Indicators use only past data. Volatility rank is a rolling window. Channels use `.shift(1)`. A signal known at today's close is held from the *next* bar (`position = signal.shift(1)`). |
| **Optimistic fills** | `fill="close"` assumes you trade at the close that produced the signal. `fill="next_open"` trades at the next open and is the one to believe. Compare both. |
| **Ignoring costs** | Fees are charged on turnover (a long→short flip pays twice), shorts pay borrow. Stress the fee rate (10 bps vs 30 bps) to see how fragile a result is. |
| **Warm-up leakage** | Data before `EVAL_START` only warms indicators up; only the scored period counts. |
| **Luck** | `sharpe_ci`, `random_timing_test` and `sharpe_diff_ci` in `portfolio/robustness.py` (see below). |

## Evaluation protocol

Follow this order before believing a result:

1. **Decide the idea and its parameters before looking at results.** Prefer conventional, documented parameters over fitted ones. Every variant you try raises the chance of a lucky winner.
2. **Test on a long history** (the robustness script uses ~20 years), not one stock over a few years.
3. **Test across many assets,** ideally diversified asset classes rather than hand-picked winners. Single stocks chosen with hindsight are survivor-biased.
4. **Split time into a tune period and a check period.** Choose settings on the first, report only the second. `research/frequency_sweep.py` does this for the original strategy; the dashboard's sweep tab warns about it.
5. **Use realistic fills and costs.** Report `next_open`, and re-run at a higher fee.
6. **Compare against baselines:** buy & hold, and a simple rule such as "close above the 200-day average". If a complicated strategy can't beat a one-line rule, use the one-line rule.
7. **Run the luck tests** (below). A good-looking Sharpe whose confidence interval includes 0 is not evidence.
8. **Look at drawdown and exposure, not just return.** A strategy that is invested 24% of the time can't be judged on the same terms as buy & hold.
9. **Paper trade** (see [PAPER_TRADING.md](PAPER_TRADING.md)) before risking real money.

## The luck tests

- **`sharpe_ci(returns)`:** block-bootstrap 95% interval for the annualised Sharpe ratio. If it includes 0, you can't tell the strategy from zero. With about 4 years of data the interval is roughly ±0.5 wide, so a Sharpe of 1.0 is hard to distinguish from 0.
- **`random_timing_test(result, fee)`:** keeps your exposure, holding periods and trade count, but circularly shifts the positions against the returns. If the actual Sharpe sits inside the shifted distribution (high p-value), the timing added nothing; the return came from simply being invested. A p-value below about 0.10 is the minimum to be interested.
- **`sharpe_diff_ci(a, b)`:** paired bootstrap of Sharpe(a) − Sharpe(b) on the same dates. If the interval includes 0, the strategy's risk-adjusted return is not provably different from buy & hold. What it may still buy you is a smaller drawdown.

Multiple testing applies: with 14 tickers, one or two will look "significant" by chance alone.

## Metrics glossary

| Metric | Meaning |
|---|---|
| `total_return` / `annual_return` | Growth of equity over the scored period, total and annualised. |
| `sharpe` | Mean daily return ÷ its standard deviation × √252. Not reduced by a risk-free rate (cash earns 0% in the engine). |
| `max_drawdown` | Worst peak-to-trough fall in equity. |
| `exposure` | Average absolute position, i.e. the share of time (and size) you are invested. |
| `turnover/yr` | Total position change per year; multiply by the fee rate for the annual cost drag. |
| `buy_hold_*` | The same metrics for simply holding the asset over the same period. |

## Research log

Results are from the project's `research.robustness` runs (2006–now, next-open fills, 10 bps unless stated). Numbers will move as data refreshes.

| Question | Finding |
|---|---|
| Does the original regime-gated strategy have an edge? | No. About 0% a year as a diversified portfolio. Negative after 30 bps. No single ticker beat random timing at p < 0.10. |
| Does shorting help? | No. Long+short lost money in every test, including on a stock that tripled (GOOGL, 2023→). |
| Why is the original so weak? | It is invested only ~23% of the time. Each sub-strategy trades in one regime only, about 20% of days are blocked as CRISIS by construction (percentile rank), and its position turns over about 16 times a year, so costs bite. |
| Does a simple trend filter hold up? | As a **portfolio** of diversified assets, yes, as drawdown control (roughly 30–85% of buy & hold's return depending on variant, far shallower drawdowns, similar or slightly lower Sharpe). On single stocks it beat buy & hold on Sharpe 0 of 14 times since 2015. |
| Does volatility targeting help? | Per-ticker average drawdown falls to about −16% (from −30 to −36% for the plain trend filter), but return and exposure also fall sharply (34–39% exposure). Fine if smoothness is the goal; the gain is smaller at portfolio level since 2015. |
| Are the findings regime-dependent? | Yes. 2006–14 contains 2008, which favours trend following. 2015–now is mostly a bull market, which penalises it. |

Not yet done: cash earning interest (the engine pays 0%), an India-tradable universe test, a walk-forward evaluation, and a tune/check split inside the dashboard sweep. See [ROADMAP.md](ROADMAP.md).
