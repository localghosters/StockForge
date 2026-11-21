def generate_signals(prices, short_window, long_window):
    df = prices.copy()
    df["sma_short"] = df["close"].rolling(short_window).mean()
    df["sma_long"] = df["close"].rolling(long_window).mean()
    df["signal"] = (df["sma_short"] > df["sma_long"]).astype(int)
    return df