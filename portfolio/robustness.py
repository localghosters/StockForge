"""Is the result skill or luck? Two cheap, honest checks."""
import numpy as np

from portfolio.metrics import sharpe_ratio


def sharpe_ci(returns, n_boot=2000, block=20, seed=0, level=0.95):
    """Block-bootstrap confidence interval for the annualised Sharpe ratio."""
    r = np.asarray(returns.dropna(), dtype=float)
    n = len(r)
    if n < 2 * block:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, (n_boot, nb))
    idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(n_boot, -1)[:, :n]
    s = r[idx]
    sd = s.std(axis=1)
    sharpes = np.where(sd > 0, s.mean(axis=1) / np.where(sd > 0, sd, 1) * np.sqrt(252), 0.0)
    lo, hi = np.percentile(sharpes, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)


def random_timing_test(result, fee_rate, n=1000, seed=0, min_shift=20):
    """Keep the exposure, holding periods and trade count; destroy the timing.

    Circularly shifts the position series against the returns. If real timing
    adds nothing, the actual Sharpe lands inside the shifted distribution.
    Close-fill approximation; ignores borrow cost.
    """
    pos = result["position"].to_numpy(dtype=float)
    ret = result["return"].fillna(0).to_numpy(dtype=float)
    days = len(pos)
    if days < 4 * min_shift:
        return {"actual_sharpe": np.nan, "median_random_sharpe": np.nan, "p_value": np.nan}
    rng = np.random.default_rng(seed)
    shifts = rng.integers(min_shift, days - min_shift, n)
    sharpes = np.empty(n)
    for i, k in enumerate(shifts):
        rolled = np.roll(pos, k)
        trade = np.abs(np.diff(rolled, prepend=rolled[0]))
        r = rolled * ret - trade * fee_rate
        sd = r.std()
        sharpes[i] = r.mean() / sd * np.sqrt(252) if sd > 0 else 0.0
    actual = sharpe_ratio(result["strategy_return"].fillna(0))
    return {
        "actual_sharpe": float(actual),
        "median_random_sharpe": float(np.median(sharpes)),
        "p_value": float((np.sum(sharpes >= actual) + 1) / (n + 1)),
    }
