import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import secretshield
import random


# ==========================================
# 1. SETTINGS
# ==========================================

ticker = "AAPL"

start_date = "2020-01-01"
end_date = "2025-01-01"

short_window = 20
long_window = 50


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

