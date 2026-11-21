import config
from data.fetch import download_prices
from database.db import create_tables, save_prices, load_prices
from strategies.sma_crossover import generate_signals
from backtesting.engine import run_backtest
from portfolio.metrics import summary
from visualisation.plots import plot_equity


def main():
    print("StockForge started")
    print("Tickers:", config.TICKERS)
    create_tables()

    for ticker in config.TICKERS:
        print(f"\n--- {ticker} ---")

        raw = download_prices(ticker, config.START_DATE, config.END_DATE)
        if raw.empty:
            print("No data found, skipping.")
            continue
        save_prices(ticker, raw)

        prices = load_prices(ticker)
        signals = generate_signals(prices, config.SHORT_WINDOW, config.LONG_WINDOW)
        result = run_backtest(signals, config.INITIAL_CAPITAL, config.FEE_RATE)

        stats = summary(result)
        for name, value in stats.items():
            print(f"{name}: {value:.2%}" if name != "sharpe" else f"{name}: {value:.2f}")

        plot_equity(result, ticker, save_path=f"{ticker}_equity.png")

    print("\nDone")


if __name__ == "__main__":
    main()