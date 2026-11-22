import pandas as pd
from strategies.regime import detect_regime
from strategies import trend_breakout, mean_reversion

ALL_STRATEGIES = [trend_breakout, mean_reversion]


def build_signal(df, strategies=None, gated=True, params=None,
                 extra_regimes=None, size=1.0, allow_short=False):
    strategies = strategies or ALL_STRATEGIES
    params = params or {}
    extra_regimes = extra_regimes or []
    out = detect_regime(df)
    sig_cols, on_cols = [], []

    for s in strategies:
        kwargs = dict(params.get(s.NAME, {}))
        kwargs["allow_short"] = allow_short
        raw = s.signal(out, **kwargs)
        if gated:
            allowed = out["regime"].isin(list(s.REGIMES) + extra_regimes)
        else:
            allowed = pd.Series(True, index=out.index)
        out[f"sig_{s.NAME}"] = raw.where(allowed, 0)
        out[f"on_{s.NAME}"] = allowed
        sig_cols.append(f"sig_{s.NAME}")
        on_cols.append(f"on_{s.NAME}")

    active = out[on_cols].sum(axis=1)
    out["signal"] = out[sig_cols].sum(axis=1) / active.clip(lower=1) * size
    return out