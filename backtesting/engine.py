def run_backtest(df, initial_capital, fee_rate, borrow_rate=0.0):
    df = df.copy()
    df["return"] = df["close"].pct_change()
    df["position"] = df["signal"].shift(1).fillna(0)
    df["trade"] = df["position"].diff().abs().fillna(0)
    df["borrow"] = (-df["position"]).clip(lower=0) * borrow_rate / 252
    df["strategy_return"] = (
        df["position"] * df["return"] - df["trade"] * fee_rate - df["borrow"]
    )
    df["equity"] = initial_capital * (1 + df["strategy_return"].fillna(0)).cumprod()
    df["buy_hold"] = initial_capital * (1 + df["return"].fillna(0)).cumprod()
    return df