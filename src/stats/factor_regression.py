"""
src/stats/factor_regression.py
Phase 4 — Factor Model Regressions:
Evaluates whether statistical arbitrage excess returns persist after controlling for:
1. CAPM (Nifty 50 market factor)
2. IIMA 4-factor model (Market, SMB, HML, WML from Agarwalla et al. 2013)

Implemented with pure, robust NumPy Newey-West (1987) HAC covariance estimation.
Zero external fragile dependencies.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional


def run_factor_regression(
    strategy_returns: pd.Series,
    factor_df: pd.DataFrame,
    rf_series: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Regresses strategy excess returns on asset pricing factors using Newey-West HAC standard errors.
    Returns:
      alpha_daily, alpha_ann, alpha_tstat, alpha_pval, r_squared, betas, t_betas
    """
    common_dates = strategy_returns.dropna().index.intersection(factor_df.dropna().index)
    if len(common_dates) < 20:
        return {
            "alpha_daily": 0.0, "alpha_ann": 0.0, "alpha_tstat": 0.0,
            "alpha_pval": 1.0, "r_squared": 0.0, "n_obs": len(common_dates), "betas": {}, "t_betas": {}
        }

    y = strategy_returns.loc[common_dates].values
    if rf_series is not None:
        rf_vals = rf_series.reindex(common_dates).fillna(0.0).values
        y = y - rf_vals

    T = len(y)
    X_raw = factor_df.loc[common_dates].values
    K = X_raw.shape[1]
    col_names = list(factor_df.columns)

    # Add intercept column (constant) as first column
    X = np.column_stack([np.ones(T), X_raw])
    k_vars = K + 1

    # OLS coefficient estimates: beta = (X'X)^(-1) X'y
    xtx = X.T @ X
    xtx_inv = np.linalg.pinv(xtx)
    beta = xtx_inv @ (X.T @ y)

    # Residuals
    residuals = y - (X @ beta)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 0.0

    # Newey-West (1987) HAC Covariance Matrix
    max_lags = int(np.floor(4.0 * (T / 100.0) ** (2.0 / 9.0)))
    max_lags = max(1, min(max_lags, T // 4))

    # Gamma_0 = sum_t (e_t^2 * x_t * x_t')
    e_x = residuals[:, None] * X  # shape (T, k_vars)
    omega = e_x.T @ e_x

    for l in range(1, max_lags + 1):
        weight = 1.0 - (l / (max_lags + 1.0))
        gamma_l = e_x[l:].T @ e_x[:-l]
        omega += weight * (gamma_l + gamma_l.T)

    v_hac = xtx_inv @ omega @ xtx_inv
    se_hac = np.sqrt(np.maximum(np.diag(v_hac), 1e-14))

    t_stats = beta / se_hac
    p_vals = 2.0 * (1.0 - stats.norm.cdf(np.abs(t_stats)))

    alpha_daily = float(beta[0])
    alpha_ann = float(alpha_daily * 252.0)
    alpha_t = float(t_stats[0])
    alpha_p = float(p_vals[0])

    betas = {col_names[i]: float(beta[i+1]) for i in range(K)}
    t_betas = {f"{col_names[i]}_tstat": float(t_stats[i+1]) for i in range(K)}

    return {
        "alpha_daily": alpha_daily,
        "alpha_ann": alpha_ann,
        "alpha_tstat": alpha_t,
        "alpha_pval": alpha_p,
        "r_squared": r2,
        "n_obs": T,
        "betas": betas,
        "t_betas": t_betas
    }
