import pandas as pd
from strategies.indicators import rsi, hold_state

NAME = "mean_reversion"
REGIMES = ["RANGE"]


def signal(df, rsi_entry=10, exit_window=5, allow_short=False):
    fast = rsi(df["close"], 2)
    avg = df["close"].rolling(exit_window).mean()

    long_in = fast < rsi_entry
    long_out = df["close"] > avg
    short_out = df["close"] < avg
    if allow_short:
        short_in = fast > 100 - rsi_entry
    else:
        short_in = pd.Series(False, index=df.index)

    states = hold_state(long_in.to_numpy(), long_out.to_numpy(),
                        short_in.to_numpy(), short_out.to_numpy())
    return pd.Series(states, index=df.index)