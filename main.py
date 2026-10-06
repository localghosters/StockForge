import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import secretshield
import random


# ==========================================
# 1. SETTINGS
# ==========================================

ticker = "AAPL"

start_date = "2015-01-01"
end_date = "2026-01-01"

short_window = 20
long_window = 50

initial_capital = 10000


# ==========================================
# 2. DOWNLOAD MARKET DATA
# ==========================================

print("Downloading market data...")

data = yf.download(
    ticker,
    start=start_date,
    end=end_date,
    auto_adjust=True
)

print("Data downloaded successfully.")
print()


# ==========================================
# 3. DISPLAY BASIC INFORMATION
# ==========================================

print("First 5 rows:")
print(data.head())

print()
print("Number of rows and columns:")
print(data.shape)

print()
print("Available columns:")
print(data.columns)

print()


# ==========================================
# 4. CALCULATE DAILY RETURNS
# ==========================================

data["Return"] = data["Close"].pct_change()


# ==========================================
# 5. CALCULATE MOVING AVERAGES
# ==========================================

data["MA20"] = data["Close"].rolling(
    window=short_window
).mean()

data["MA50"] = data["Close"].rolling(
    window=long_window
).mean()


# ==========================================
# 6. GENERATE BUY / SELL SIGNALS
# ==========================================

data["Signal"] = 0

data.loc[
    data["MA20"] > data["MA50"],
    "Signal"
] = 1

data.loc[
    data["MA20"] < data["MA50"],
    "Signal"
] = -1


# ==========================================
# 7. CALCULATE STRATEGY RETURNS
# ==========================================

data["Strategy Return"] = (
    data["Return"] * data["Signal"].shift(1)
)


# ==========================================
# 8. CALCULATE CUMULATIVE RETURNS
# ==========================================

data["Market Growth"] = (
    1 + data["Return"]
).cumprod()

data["Strategy Growth"] = (
    1 + data["Strategy Return"].fillna(0)
).cumprod()


# ==========================================
# 9. BASIC PERFORMANCE STATISTICS
# ==========================================

market_return = (
    data["Market Growth"].iloc[-1] - 1
) * 100

strategy_return = (
    data["Strategy Growth"].iloc[-1] - 1
) * 100


print("==========================================")
print("STOCKFORGE RESULTS")
print("==========================================")

print(f"Ticker: {ticker}")
print(f"Period: {start_date} to {end_date}")
print()

print(f"Buy & Hold Return: {market_return:.2f}%")
print(f"Strategy Return:   {strategy_return:.2f}%")
print()


# ==========================================
# 10. FIND BUY / SELL SIGNAL CHANGES
# ==========================================

data["Signal Change"] = data["Signal"].diff()

buy_signals = data[data["Signal Change"] == 2]
sell_signals = data[data["Signal Change"] == -2]


print(f"Buy signals:  {len(buy_signals)}")
print(f"Sell signals: {len(sell_signals)}")
print()


# ==========================================
# 11. CALCULATE MAX DRAWDOWN
# ==========================================

peak = data["Strategy Growth"].cummax()

drawdown = (
    data["Strategy Growth"] - peak
) / peak

max_drawdown = drawdown.min() * 100

print(f"Maximum Drawdown: {max_drawdown:.2f}%")
print()


# ==========================================
# 12. RISK & PERFORMANCE ANALYSIS
# ==========================================

years = (
    data.index[-1] - data.index[0]
).days / 365.25

cagr = (
    data["Strategy Growth"].iloc[-1] ** (1 / years) - 1
) * 100

annualized_volatility = (
    data["Strategy Return"].std() * (252 ** 0.5)
) * 100

if annualized_volatility != 0:
    sharpe_ratio = (
        data["Strategy Return"].mean()
        / data["Strategy Return"].std()
    ) * (252 ** 0.5)
else:
    sharpe_ratio = 0


winning_days = (
    data["Strategy Return"] > 0
).sum()

active_days = (
    data["Strategy Return"] != 0
).sum()

if active_days > 0:
    win_rate = (
        winning_days / active_days
    ) * 100
else:
    win_rate = 0


print("==========================================")
print("RISK ANALYSIS")
print("==========================================")

print(
    f"CAGR:                   "
    f"{cagr:.2f}%"
)
)

print(
    f"Annualized Volatility:  "
    f"{annualized_volatility:.2f}%"
)

print(
    f"Sharpe Ratio:           "
    f"{sharpe_ratio:.2f}"
)

print(
    f"Strategy Win Rate:      "
    f"{win_rate:.2f}%"
)

print()


# ==========================================
# 13. PORTFOLIO VALUE SIMULATION
# ==========================================

data["Portfolio Value"] = (
    initial_capital *
    data["Strategy Growth"]
)


final_portfolio_value = (
    data["Portfolio Value"].iloc[-1]
)


print("==========================================")
print("PORTFOLIO SIMULATION")
print("==========================================")

print(
    f"Initial Capital: "
    f"${initial_capital:,.2f}"
)

print(
    f"Final Portfolio: "
    f"${final_portfolio_value:,.2f}"
)

print(
    f"Profit / Loss:    "
    f"${final_portfolio_value - initial_capital:,.2f}"
)

print()


# ==========================================
# 14. PLOT STOCK PRICE + MOVING AVERAGES
# ==========================================

plt.figure(figsize=(14, 7))

plt.plot(
    data.index,
    data["Close"],
    label=f"{ticker} Price"
)

plt.plot(
    data.index,
    data["MA20"],
    label="20-Day MA"
)

plt.plot(
    data.index,
    data["MA50"],
    label="50-Day MA"
)

plt.scatter(
    buy_signals.index,
    buy_signals["Close"],
    marker="^",
    s=80,
    label="Buy"
)

plt.scatter(
    sell_signals.index,
    sell_signals["Close"],
    marker="v",
    s=80,
    label="Sell"
)

plt.title(
    f"{ticker} StockForge Moving Average Strategy"
)

plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid()

plt.show()


# ==========================================
# 15. PLOT STRATEGY PERFORMANCE
# ==========================================

plt.figure(figsize=(14, 7))

plt.plot(
    data.index,
    data["Market Growth"],
    label="Buy & Hold"
)

plt.plot(
    data.index,
    data["Strategy Growth"],
    label="StockForge Strategy"
)

plt.title(
    f"{ticker} Strategy Performance"
)

plt.xlabel("Date")
plt.ylabel("Growth")

plt.legend()
plt.grid()

plt.show()


# ==========================================
# 16. PLOT PORTFOLIO VALUE
# ==========================================

plt.figure(figsize=(14, 7))

plt.plot(
    data.index,
    data["Portfolio Value"],
    label="Portfolio Value"
)

plt.axhline(
    initial_capital,
    linestyle="--",
    label="Initial Capital"
)

plt.title(
    f"{ticker} Portfolio Growth"
)

plt.xlabel("Date")
plt.ylabel("Portfolio Value ($)")

plt.legend()
plt.grid()

plt.show()


# ==========================================
# 17. FINAL DATA PREVIEW
# ==========================================

print("Final 10 rows:")

print(
    data[
        [
            "Close",
            "Return",
            "MA20",
            "MA50",
            "Signal",
            "Strategy Return",
            "Market Growth",
            "Strategy Growth",
            "Portfolio Value"
        ]
    ].tail(10)
)
