"""
tests/test_placebo_pl1.py
Placebo Test PL1: Planted Cointegrated Pairs.
Verifies that the strategy reliably identifies and profits from known mean-reverting cointegrated series.
Hard Fail: ADF test fails to reject unit root (p >= 0.05) or strategy produces negative gross return on planted pair.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from src.strategies.gatev import simulate_pair_trading


def test_planted_cointegrated_pair_pl1():
    np.random.seed(42)
    n_days = 252
    dates = pd.date_range("2021-01-01", periods=n_days, freq="B")

    # Construct shared stochastic trend (random walk)
    rw = np.cumsum(np.random.normal(0, 0.015, n_days)) + 100.0

    # Construct stationary mean-reverting spread (AR(1) with phi=0.75)
    spread = np.zeros(n_days)
    for t in range(1, n_days):
        spread[t] = 0.75 * spread[t-1] + np.random.normal(0, 1.5)

    p_a = pd.Series(rw + 0.5 * spread, index=dates)
    p_b = pd.Series(rw - 0.5 * spread, index=dates)

    # 1. Statistical verification: ADF test on spread
    adf_res = adfuller(p_a.values - p_b.values)
    p_val = adf_res[1]
    assert p_val < 0.05, f"PL1 FAIL: ADF did not reject unit root on planted spread (p={p_val:.4f})"

    # 2. Strategy verification: run pairs trading on planted series
    formation_std = float(np.std(p_a.values / p_a.values[0] - p_b.values / p_b.values[0]))
    ret_series, trades = simulate_pair_trading(
        p_a, p_b,
        spread_std=formation_std,
        entry_sigma=1.5,
        exit_threshold=0.0
    )

    total_gross = ret_series.sum()
    assert len(trades) > 0, "PL1 FAIL: Strategy did not trigger any trades on planted cointegrated pair"
    assert total_gross > 0, f"PL1 FAIL: Strategy produced negative return ({total_gross:.4f}) on cointegrated pair"
