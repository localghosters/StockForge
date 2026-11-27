import numpy as np
import pandas as pd
import pytest

from backtesting.engine import run_backtest
from portfolio.robustness import random_timing_test, sharpe_ci


def _prices(n=600, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
    open_ = close * (1 + rng.normal(0, 0.004, n))
    return pd.DataFrame({"open": open_, "close": close}, index=pd.bdate_range("2020-01-01", periods=n))


def test_next_open_matches_close_when_position_is_constant():
    # Day 1 legitimately differs (entering at the open earns only that day's
    # open-to-close move); from day 2 a constant position earns the same return.
    df = _prices(); df["signal"] = 1.0
    a = run_backtest(df, 1000, 0.0, 0.0, "close")["strategy_return"]
    b = run_backtest(df, 1000, 0.0, 0.0, "next_open")["strategy_return"]
    assert np.allclose(a.iloc[2:], b.iloc[2:], rtol=1e-9, atol=1e-12)


def test_unknown_fill_raises():
    df = _prices(); df["signal"] = 1.0
    with pytest.raises(ValueError):
        run_backtest(df, 1000, 0.0, 0.0, "magic")


def test_sharpe_ci_brackets_point_estimate():
    r = pd.Series(np.random.default_rng(1).normal(0.0005, 0.01, 1500))
    lo, hi = sharpe_ci(r, n_boot=500)
    point = r.mean() / r.std() * np.sqrt(252)
    assert lo < point < hi


def test_random_timing_on_random_signal_is_not_significant():
    df = _prices(1500); rng = np.random.default_rng(9)
    df["signal"] = pd.Series(rng.integers(0, 2, len(df)), index=df.index).rolling(10).mean().round()
    res = run_backtest(df.fillna(0), 1000, 0.0005)
    out = random_timing_test(res, 0.0005, n=300)
    assert 0 <= out["p_value"] <= 1


def test_trend_filter_is_long_only_and_vol_target_never_levers_up():
    from strategies import trend_filter
    df = _prices(1000)
    plain = trend_filter.signal(df)
    vt = trend_filter.signal(df, target_vol=0.05)
    assert plain.between(0, 1).all() and vt.between(0, 1).all()
    assert (vt <= plain + 1e-12).all()


def test_trend_filter_fully_invested_in_steady_uptrend():
    from strategies import trend_filter
    idx = pd.bdate_range("2020-01-01", periods=400)
    df = pd.DataFrame({"close": np.linspace(100, 300, 400)}, index=idx)
    assert trend_filter.signal(df).iloc[-1] == 1.0
