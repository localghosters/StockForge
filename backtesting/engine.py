def run_backtest(df, initial_capital, fee_rate, borrow_rate=0.0, fill="close"):
    """fill='close': trade at the close that produced the signal (optimistic).
    fill='next_open': trade at the next day's open (needs an 'open' column)."""
    df = df.copy()
    df["return"] = df["close"].pct_change()
    df["position"] = df["signal"].shift(1).fillna(0)
    df["trade"] = df["position"].diff().abs().fillna(0)
    df["borrow"] = (-df["position"]).clip(lower=0) * borrow_rate / 252
    if fill == "next_open":
        prev = df["position"].shift(1).fillna(0)
        overnight = df["open"] / df["close"].shift(1) - 1
        intraday = df["close"] / df["open"] - 1
        gross = (1 + prev * overnight) * (1 + df["position"] * intraday) - 1
    elif fill == "close":
        gross = df["position"] * df["return"]
    else:
        raise ValueError(f"unknown fill model: {fill}")
    df["strategy_return"] = gross - df["trade"] * fee_rate - df["borrow"]
    df["equity"] = initial_capital * (1 + df["strategy_return"].fillna(0)).cumprod()
    df["buy_hold"] = initial_capital * (1 + df["return"].fillna(0)).cumprod()
    return df