"""
tests/test_stats.py
Unit tests for statistical inference: Newey-West t-stats, DSR, and Factor regression.
"""

import numpy as np
import pandas as pd
from src.stats.inference import newey_west_tstat, stationary_bootstrap_ci
from src.stats.multiple_testing import compute_deflated_sharpe_ratio, adjust_pvalues_fdr
from src.stats.factor_regression import run_factor_regression


def test_newey_west_tstat():
    np.random.seed(42)
    ar1 = np.zeros(200)
    for t in range(1, 200):
        ar1[t] = 0.5 * ar1[t-1] + np.random.normal(0.001, 0.01)
    
    t_stat, p_val, se = newey_west_tstat(pd.Series(ar1))
    assert np.isfinite(t_stat)
    assert 0.0 <= p_val <= 1.0
    assert se > 0


def test_deflated_sharpe_ratio():
    dsr_high = compute_deflated_sharpe_ratio(sr_estimate=1.5, n_trials=1, var_sr=0.1, t_obs=1000)
    assert dsr_high > 0.95

    dsr_diluted = compute_deflated_sharpe_ratio(sr_estimate=0.5, n_trials=1000, var_sr=0.25, t_obs=500)
    assert dsr_diluted < dsr_high


def test_fdr_adjustment():
    p_vals = np.array([0.001, 0.01, 0.04, 0.08, 0.50])
    q_vals = adjust_pvalues_fdr(p_vals)
    assert len(q_vals) == len(p_vals)
    assert (q_vals >= p_vals).all()


def test_factor_regression():
    np.random.seed(123)
    dates = pd.date_range("2022-01-01", periods=100, freq="B")
    mkt = np.random.normal(0.0005, 0.01, 100)
    smb = np.random.normal(0.0001, 0.005, 100)
    # y has alpha = 0.0004 daily (approx 10% ann) plus market beta = 0.3
    y = 0.0004 + 0.3 * mkt + np.random.normal(0, 0.002, 100)

    strat = pd.Series(y, index=dates)
    factors = pd.DataFrame({"mkt": mkt, "smb": smb}, index=dates)

    res = run_factor_regression(strat, factors)
    assert np.isclose(res["betas"]["mkt"], 0.3, atol=0.1)
    assert res["alpha_daily"] > 0
    assert res["r_squared"] > 0.3
    assert res["n_obs"] == 100
