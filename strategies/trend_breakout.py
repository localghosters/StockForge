import pandas as pd
from strategies.indicators import hold_state

NAME = "trend_breakout"
REGIMES = ["TREND"]


def signal(df, entry_window=20, exit_window=10, allow_short=False):
    high_in = df["high"].rolling(entry_window).max().shift(1)
    low_in = df["low"].rolling(entry_window).min().shift(1)
    high_out = df["high"].rolling(exit_window).max().shift(1)
    low_out = df["low"].rolling(exit_window).min().shift(1)

    long_in = df["close"] > high_in
    long_out = df["close"] < low_out
    short_out = df["close"] > high_out
    if allow_short:
        short_in = df["close"] < low_in
    else:
        short_in = pd.Series(False, index=df.index)

    states = hold_state(long_in.to_numpy(), long_out.to_numpy(),
                        short_in.to_numpy(), short_out.to_numpy())
    return pd.Series(states, index=df.index)