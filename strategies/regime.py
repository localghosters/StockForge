import pandas as pd
import config
from strategies.indicators import adx, vol_rank


def detect_regime(df):
    out = df.copy()
    out["adx"] = adx(out)
    out["vol_rank"] = vol_rank(out["close"])

    regime = pd.Series("NEUTRAL", index=out.index)
    regime[out["adx"] >= config.ADX_TREND] = "TREND"
    regime[out["adx"] <= config.ADX_RANGE] = "RANGE"
    regime[out["vol_rank"] >= config.VOL_CAP] = "CRISIS"
    regime[out["adx"].isna() | out["vol_rank"].isna()] = "WARMUP"

    out["regime"] = regime
    return out