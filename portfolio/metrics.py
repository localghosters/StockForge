import numpy as np


def total_return(equity):
    return equity.iloc[-1] / equity.iloc[0] - 1


def annual_return(equity):
    years = len(equity) / 252
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1


def sharpe_ratio(returns):
    std = returns.std()
    if std == 0:
        return 0.0
    return returns.mean() / std * np.sqrt(252)


def max_drawdown(equity):
    peak = equity.cummax()
    return ((equity - peak) / peak).min()


def summary(df):
    return {
        "total_return": total_return(df["equity"]),
        "annual_return": annual_return(df["equity"]),
        "sharpe": sharpe_ratio(df["strategy_return"].fillna(0)),
        "max_drawdown": max_drawdown(df["equity"]),
        "buy_hold_return": total_return(df["buy_hold"]),
        "buy_hold_drawdown": max_drawdown(df["buy_hold"]),
    }


def regime_breakdown(df):
    tmp = df.assign(prev_regime=df["regime"].shift(1))
    tmp["strategy_return"] = tmp["strategy_return"].fillna(0)
    return tmp.groupby("prev_regime")["strategy_return"].agg(
        days="count",
        avg_daily="mean",
        total=lambda x: (1 + x).prod() - 1,
    )
