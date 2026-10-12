"""
tests/test_placebo_pl2.py
Placebo Test PL2: Random Pair Placebo.
Verifies that the strategy does NOT generate statistically significant profits on purely independent random walks.
Hard Fail: abs(t-stat) >= 1.65 on independent random pairs (indicates snooping, leak, or coding artifact).
"""

import numpy as np
import pandas as pd
from scipy import stats
from src.strategies.gatev import simulate_pair_trading


def test_random_pairs_zero_alpha_pl2():
    np.random.seed(123)
    n_days = 252
    n_pairs = 20
    dates = pd.date_range("2021-01-01", periods=n_days, freq="B")

    daily_portfolio_returns = np.zeros(n_days)

    for i in range(n_pairs):
        # Generate two completely independent random walks
        ret_a = np.random.normal(0.0003, 0.015, n_days)
        ret_b = np.random.normal(0.0003, 0.015, n_days)
        p_a = pd.Series(100.0 * np.exp(np.cumsum(ret_a)), index=dates)
        p_b = pd.Series(100.0 * np.exp(np.cumsum(ret_b)), index=dates)

        # In formation window, measure spread std
        spread_std = float(np.std(p_a.values / p_a.values[0] - p_b.values / p_b.values[0]))
        ret_series, _ = simulate_pair_trading(
            p_a, p_b,
            spread_std=spread_std,
            entry_sigma=2.0,
            exit_threshold=0.0
        )
        daily_portfolio_returns += ret_series.values / n_pairs

    # Calculate t-statistic against null hypothesis of 0 mean return
    active_days = daily_portfolio_returns[daily_portfolio_returns != 0]
    if len(active_days) > 10:
        t_stat, p_val = stats.ttest_1samp(active_days, 0.0)
    else:
        t_stat = 0.0

    # PL2 Pass Criterion: |t-stat| < 1.65 (not significant at 10% level)
    assert abs(t_stat) < 1.65, (
        f"PL2 HARD FAIL: Strategy earned statistically significant return on independent random walks! "
        f"t-stat = {t_stat:.4f} (must be < 1.65)"
    )
