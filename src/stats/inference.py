"""
src/stats/inference.py
Phase 4 — Statistical Inference Engine:
1. Newey-West (1987) HAC t-statistic and standard errors for autocorrelated return series.
2. Politis & Romano (1994) stationary bootstrap confidence intervals.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional


def newey_west_tstat(returns: pd.Series, max_lags: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Computes Newey-West (1987) heteroskedasticity and autocorrelation consistent (HAC)
    t-statistic and p-value for the null hypothesis that mean return is 0.
    Returns:
      t_stat: Newey-West t-statistic
      p_value: two-sided p-value
      se_hac: HAC standard error of the mean
    """
    r = returns.dropna().values
    T = len(r)
    if T < 5:
        return 0.0, 1.0, 1.0

    mean_r = np.mean(r)
    e = r - mean_r

    # Rule of thumb for lag length: floor(4 * (T / 100)^(2/9))
    if max_lags is None:
        max_lags = int(np.floor(4.0 * (T / 100.0) ** (2.0 / 9.0)))
    max_lags = max(1, min(max_lags, T // 4))

    # Variance component: gamma_0 + 2 * sum( (1 - l / (L+1)) * gamma_l )
    gamma_0 = np.sum(e ** 2) / T
    var_hac = gamma_0

    for l in range(1, max_lags + 1):
        weight = 1.0 - (l / (max_lags + 1.0))  # Bartlett kernel
        gamma_l = np.sum(e[l:] * e[:-l]) / T
        var_hac += 2.0 * weight * gamma_l

    var_hac = max(var_hac, 1e-12)
    se_hac = np.sqrt(var_hac / T)

    t_stat = mean_r / se_hac
    p_val = 2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=T - 1))

    return float(t_stat), float(p_val), float(se_hac)


def stationary_bootstrap_ci(
    returns: pd.Series,
    n_boot: int = 1000,
    expected_block_size: float = 10.0,
    alpha: float = 0.05,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Politis & Romano (1994) Stationary Bootstrap for annualized Sharpe ratio.
    Block length follows Geometric distribution with mean expected_block_size.
    Returns:
      point_estimate: sample annualized Sharpe
      ci_lower: (alpha/2) quantile
      ci_upper: (1 - alpha/2) quantile
    """
    r = returns.dropna().values
    T = len(r)
    if T < 10 or np.std(r) == 0:
        return 0.0, 0.0, 0.0

    point_sharpe = float(np.mean(r) / np.std(r) * np.sqrt(252))

    rng = np.random.default_rng(seed)
    p_geom = 1.0 / expected_block_size

    boot_sharpes = []

    for _ in range(n_boot):
        # Generate stationary bootstrap indices
        indices = np.zeros(T, dtype=int)
        idx = rng.integers(0, T)
        for t in range(T):
            if rng.random() < p_geom:
                idx = rng.integers(0, T)
            else:
                idx = (idx + 1) % T
            indices[t] = idx

        resampled_r = r[indices]
        s_std = np.std(resampled_r)
        if s_std > 1e-8:
            b_sharpe = np.mean(resampled_r) / s_std * np.sqrt(252)
            boot_sharpes.append(b_sharpe)

    if not boot_sharpes:
        return point_sharpe, point_sharpe, point_sharpe

    ci_lower = float(np.percentile(boot_sharpes, 100 * (alpha / 2.0)))
    ci_upper = float(np.percentile(boot_sharpes, 100 * (1.0 - alpha / 2.0)))

    return point_sharpe, ci_lower, ci_upper
