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

