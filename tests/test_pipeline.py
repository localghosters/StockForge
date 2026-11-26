import numpy as np
import pandas as pd
import pytest
from backtesting.pipeline import run_pipeline


def synthetic_prices(n=1200, seed=7):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, n)))
    spread = close * rng.uniform(0.002, 0.012, n)
    idx = pd.bdate_range("2019-01-01", periods=n)
    return pd.DataFrame({
        "open": close * (1 + rng.normal(0, 0.003, n)),
        "high": close + spread, "low": close - spread,
        "close": close, "volume": rng.integers(1_000, 5_000, n),
    }, index=idx)


def test_pipeline_returns_all_sections():
    out = run_pipeline(synthetic_prices(), "2021-01-01", 100_000, 0.001, 0.02, True)
    assert set(out) == {"result", "trades", "actions", "summary", "stats",
                        "regimes", "contrib", "yearly"}
    res = out["result"]
    assert res.index[0] >= pd.Timestamp("2021-01-01")
    for col in ("equity", "buy_hold", "position", "regime", "close"):
        assert col in res.columns
    assert res["equity"].iloc[0] == pytest.approx(100_000)


def test_pipeline_respects_allow_short():
    prices = synthetic_prices()
    long_only = run_pipeline(prices, "2021-01-01", 1000, 0.0, 0.0, False)["result"]
    assert (long_only["position"] >= 0).all()


def test_strategy_params_change_results():
    prices = synthetic_prices()
    a = run_pipeline(prices, "2021-01-01", 1000, 0.001)["summary"]
    b = run_pipeline(prices, "2021-01-01", 1000, 0.001,
                     strategy_params={"trend_breakout": {"entry_window": 60}})["summary"]
    assert a != b


def test_sweep_grid_shape_and_config_restored():
    import config
    from backtesting.pipeline import sweep_grid
    before = config.ADX_TREND
    grid = sweep_grid(synthetic_prices(), "2021-01-01", 1000, 0.001, 0.0, False,
                      "Breakout entry window", [10, 20, 40],
                      "ADX trend threshold", [20, 25], "Sharpe")
    assert grid.shape == (2, 3)
    assert grid.notna().all().all()
    assert config.ADX_TREND == before
