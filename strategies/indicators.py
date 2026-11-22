import numpy as np
import pandas as pd


def true_range(df):
    prev_close = df["close"].shift(1)
    parts = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1)
    return parts.max(axis=1)


def adx(df, window=14):
    alpha = 1 / window
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = true_range(df).ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False).mean() / tr
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False).mean() / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=alpha, adjust=False).mean()


def rsi(close, window=2):
    alpha = 1 / window
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=alpha, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=alpha, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)


def vol_rank(close, window=20, lookback=252):
    vol = close.pct_change().rolling(window).std()
    return vol.rolling(lookback).rank(pct=True)

def hold_state(long_in, long_out, short_in, short_out):
    pos = 0
    states = []
    for li, lo, si, so in zip(long_in, long_out, short_in, short_out):
        if pos == 0:
            if li:
                pos = 1
            elif si:
                pos = -1
        elif pos == 1:
            if si:
                pos = -1
            elif lo:
                pos = 0
        else:
            if li:
                pos = 1
            elif so:
                pos = 0
        states.append(pos)
    return states