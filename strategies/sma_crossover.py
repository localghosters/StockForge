import numpy as np


def generate_signals(prices, short_window, long_window, allow_short=False):
    df = prices.copy()
    df["sma_short"] = df["close"].rolling(short_window).mean()
    df["sma_long"] = df["close"].rolling(long_window).mean()

    down_value = -1 if allow_short else 0
    df["signal"] = np.where(df["sma_short"] > df["sma_long"], 1, down_value)
    df.loc[df["sma_long"].isna(), "signal"] = 0
    return df