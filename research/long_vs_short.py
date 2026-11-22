import pandas as pd
import config
from data.fetch import download_prices
from database.db import create_tables, save_prices, load_prices
from strategies.selector import build_signal
from backtesting.engine import run_backtest
from portfolio.metrics import summary
from portfolio.diagnostics import (
    trade_log, action_log, trade_stats, regime_table,
    strategy_contribution, yearly_table,
)

RESULTS_DIR = config.BASE_DIR / "results"


def print_settings():
    print("Settings")
    print(f"  data from {config.START_DATE}, scored from {config.EVAL_START}")
    print(f"  ADX trend {config.ADX_TREND}, ADX range {config.ADX_RANGE}, volatility cap {config.VOL_CAP}")
    print(f"  fee rate {config.FEE_RATE}, starting capital {config.INITIAL_CAPITAL}")
    print(f"  shorting {config.ALLOW_SHORT}, borrow rate {config.SHORT_BORROW_RATE}")


def main():
    print("StockForge started")
    print("Tickers:", config.TICKERS)
    print_settings()
    create_tables()
    if config.SAVE_FILES:
        RESULTS_DIR.mkdir(exist_ok=True)

    for ticker in config.TICKERS:
        print(f"\n=== {ticker} ===")

        raw = download_prices(ticker, config.START_DATE, config.END_DATE)
        if raw.empty:
            print("No data found, skipping.")
            continue
        save_prices(ticker, raw)

        prices = load_prices(ticker)
        signals = build_signal(prices, allow_short=config.ALLOW_SHORT)
        signals = signals.loc[config.EVAL_START:]
        result = run_backtest(signals, config.INITIAL_CAPITAL, config.FEE_RATE,
                              config.SHORT_BORROW_RATE)
        trades = trade_log(result)

        print("\nRegime table (stock = what the stock did on those days)")
        print(regime_table(result, config.FEE_RATE).round(4))

        print("\nReturn of each strategy before fees")
        for name, value in strategy_contribution(result).items():
            print(f"  {name}: {value:.2%}")

        print("\nTrade statistics")
        print(pd.Series(trade_stats(trades, result, config.FEE_RATE)).round(3).to_string())

        print("\nResults by side (return is per trade)")
        if len(trades):
            print(trades.groupby("side")["return"]
                  .agg(trades="count", avg="mean", best="max", worst="min").round(4))

        print("\nLast 8 actions")
        print(action_log(result).tail(8).to_string(index=False))

        print("\nYear by year")
        print(yearly_table(result).round(3))

        print("\nSummary")
        for name, value in summary(result).items():
            print(f"  {name}: {value:.2f}" if name == "sharpe" else f"  {name}: {value:.2%}")

        if config.SAVE_FILES:
            from visualisation.plots import plot_equity
            trades.to_csv(RESULTS_DIR / f"{ticker}_trades.csv", index=False)
            result.to_csv(RESULTS_DIR / f"{ticker}_daily.csv")
            plot_equity(result, ticker, save_path=RESULTS_DIR / f"{ticker}_equity.png")

    print("\nDone")


if __name__ == "__main__":
    main()