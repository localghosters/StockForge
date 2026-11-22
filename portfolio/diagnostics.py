import numpy as np
import pandas as pd


def _compound(x):
    return (1 + x).prod() - 1


def trade_log(df):
    cols = ["entry", "exit", "side", "days", "return",
            "regime_at_entry", "strategy_at_entry"]
    side = np.sign(df["position"])
    held = side != 0
    episode = (side != side.shift(fill_value=0)).cumsum()
    sig_cols = [c for c in df.columns if c.startswith("sig_")]
    prev_sig = df[sig_cols].shift(1)
    prev_regime = df["regime"].shift(1)

    rows = []
    for _, chunk in df[held].groupby(episode[held]):
        start = chunk.index[0]
        names = [c[4:] for c in sig_cols if prev_sig.loc[start, c] != 0]
        rows.append({
            "entry": start,
            "exit": chunk.index[-1],
            "side": "LONG" if side.loc[start] > 0 else "SHORT",
            "days": len(chunk),
            "return": _compound(chunk["strategy_return"].fillna(0)),
            "regime_at_entry": prev_regime.loc[start],
            "strategy_at_entry": "+".join(names),
        })
    return pd.DataFrame(rows, columns=cols)


def action_log(df):
    cols = ["date", "action", "from", "to", "price", "regime"]
    pos = df["position"]
    prev = pos.shift(1).fillna(0)
    prev_close = df["close"].shift(1)
    prev_regime = df["regime"].shift(1)
    changed = (pos - prev).abs() > 1e-9

    rows = []
    for date in df.index[changed]:
        p, q = prev.loc[date], pos.loc[date]
        if p == 0:
            action = "BUY" if q > 0 else "SHORT"
        elif q == 0:
            action = "SELL" if p > 0 else "COVER"
        elif p > 0 > q:
            action = "SELL and SHORT"
        elif p < 0 < q:
            action = "COVER and BUY"
        else:
            action = "ADD" if abs(q) > abs(p) else "REDUCE"
        rows.append({
            "date": date, "action": action,
            "from": round(p, 2), "to": round(q, 2),
            "price": round(prev_close.loc[date], 2),
            "regime": prev_regime.loc[date],
        })
    return pd.DataFrame(rows, columns=cols)


def trade_stats(trades, df, fee_rate):
    out = {
        "trades": len(trades),
        "time_in_market": (df["position"] != 0).mean(),
        "fees_drag": (df["trade"] * fee_rate).sum(),
        "borrow_drag": df["borrow"].sum() if "borrow" in df else 0.0,
    }
    if len(trades):
        wins = trades[trades["return"] > 0]
        losses = trades[trades["return"] <= 0]
        out["win_rate"] = len(wins) / len(trades)
        out["avg_win"] = wins["return"].mean() if len(wins) else 0.0
        out["avg_loss"] = losses["return"].mean() if len(losses) else 0.0
        out["avg_days_held"] = trades["days"].mean()
    return out


def regime_table(df, fee_rate):
    tmp = df.assign(prev_regime=df["regime"].shift(1))
    tmp["ret"] = tmp["return"].fillna(0)
    tmp["strat"] = tmp["strategy_return"].fillna(0)
    tmp["fees"] = tmp["trade"] * fee_rate
    g = tmp.groupby("prev_regime")
    return pd.DataFrame({
        "days": g.size(),
        "in_market": g["position"].apply(lambda x: (x != 0).mean()),
        "strategy": g["strat"].apply(_compound),
        "stock": g["ret"].apply(_compound),
        "fees": g["fees"].sum(),
    })


def strategy_contribution(df):
    on_cols = [c for c in df.columns if c.startswith("on_")]
    active = df[on_cols].sum(axis=1).clip(lower=1)
    out = {}
    for col in [c for c in df.columns if c.startswith("sig_")]:
        weight = (df[col] / active).shift(1).fillna(0)
        out[col[4:]] = _compound(weight * df["return"].fillna(0))
    return out


def yearly_table(df):
    years = df.index.year
    return pd.DataFrame({
        "strategy": (1 + df["strategy_return"].fillna(0)).groupby(years).prod() - 1,
        "buy_hold": (1 + df["return"].fillna(0)).groupby(years).prod() - 1,
    })