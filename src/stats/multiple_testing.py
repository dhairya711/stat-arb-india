"""
src/stats/multiple_testing.py
Phase 4 — Multiple Testing Corrections:
1. Deflated Sharpe Ratio (DSR) (Bailey and Lopez de Prado, 2014).
   Adjusts Sharpe ratio for selection bias under N backtest trials.
2. Benjamini-Hochberg False Discovery Rate (FDR) adjustment.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List


def expected_maximum_sharpe(n_trials: int, var_sr: float) -> float:
    """
    Computes expected maximum Sharpe ratio under the null hypothesis of 0 skill
    across N independent/correlated trials (Bailey and Lopez de Prado, 2014).
    E[max_N] = sqrt(var_sr) * ((1 - gamma) * Phi^{-1}(1 - 1/N) + gamma * Phi^{-1}(1 - 1/(N*e)))
    where gamma is the Euler-Mascheroni constant (~0.57721566).
    """
    if n_trials <= 1:
        return 0.0

    gamma = 0.57721566490153286
    std_sr = np.sqrt(max(var_sr, 1e-8))

    z1 = stats.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1.0 - 1.0 / (n_trials * np.e))

    e_max = std_sr * ((1.0 - gamma) * z1 + gamma * z2)
    return float(max(0.0, e_max))


def compute_deflated_sharpe_ratio(
    sr_estimate: float,
    n_trials: int,
    var_sr: float,
    t_obs: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0
) -> float:
    """
    Computes the Deflated Sharpe Ratio (DSR).
    Returns DSR probability in [0, 1].
    DSR > 0.95 corresponds to statistical significance at 5% level after multiple testing adjustment.
    """
    if t_obs < 10 or n_trials < 1:
        return 0.5

    e_max = expected_maximum_sharpe(n_trials, var_sr)

    # Standard error of the Sharpe ratio under non-normality (Mertens 2002)
    # sigma_SR = sqrt( (1 - skew * SR + (kurt - 1)/4 * SR^2) / (T - 1) )
    var_mertens = (1.0 - skewness * sr_estimate + ((kurtosis - 1.0) / 4.0) * (sr_estimate ** 2)) / (t_obs - 1.0)
    se_sr = np.sqrt(max(var_mertens, 1e-12))

    z = (sr_estimate - e_max) / se_sr
    dsr = float(stats.norm.cdf(z))
    return dsr


def adjust_pvalues_fdr(p_values: np.ndarray) -> np.ndarray:
    """
    Benjamini-Hochberg False Discovery Rate (FDR) adjustment.
    Returns adjusted p-values (q-values).
    """
    p_arr = np.asarray(p_values)
    n = len(p_arr)
    if n == 0:
        return np.array([])

    order = np.argsort(p_arr)
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(1, n + 1)

    q_vals = p_arr * n / ranks
    # Enforce monotonicity
    q_vals_sorted = q_vals[order]
    for i in range(n - 2, -1, -1):
        q_vals_sorted[i] = min(q_vals_sorted[i], q_vals_sorted[i + 1])
    
    q_out = np.empty(n)
    q_out[order] = np.minimum(q_vals_sorted, 1.0)
    return q_out
