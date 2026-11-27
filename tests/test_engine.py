import pandas as pd
import pytest
from backtesting.engine import run_backtest


def test_cash_signal_keeps_capital_unchanged():
    df = pd.DataFrame({"close": [100, 101, 102, 103], "signal": [0, 0, 0, 0]})
    out = run_backtest(df, 1000, 0.0)
    assert out["equity"].iloc[-1] == 1000


def test_always_invested_matches_price_change():
    df = pd.DataFrame({"close": [100, 101, 102, 103], "signal": [1, 1, 1, 1]})
    out = run_backtest(df, 1000, 0.0)
    assert out["equity"].iloc[-1] == pytest.approx(1030)
