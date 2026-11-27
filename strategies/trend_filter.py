"""Long-only trend filter: the one idea with decades of out-of-sample evidence.

Votes across lookbacks (default 50/100/200 days, fixed in advance, not tuned):
position = fraction of lookbacks where close is above its moving average, so it
scales in and out instead of flipping all-or-nothing. Optional volatility
targeting only ever *reduces* exposure (never leverages above 1x).
"""
import numpy as np

NAME = "trend_filter"
REGIMES = ["TREND", "RANGE", "NEUTRAL", "CRISIS", "WARMUP"]  # always on


def signal(df, lookbacks=(50, 100, 200), target_vol=None, vol_window=60,
           allow_short=False):  # allow_short accepted for selector compatibility; ignored
    close = df["close"]
    votes = sum((close > close.rolling(n).mean()).astype(float) for n in lookbacks) / len(lookbacks)
    if target_vol:
        vol = close.pct_change().rolling(vol_window).std() * np.sqrt(252)
        votes = votes * (target_vol / vol).clip(upper=1.0).fillna(0.0)
    return votes
