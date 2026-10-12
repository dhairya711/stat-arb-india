"""
src/strategies/pca_ou.py
Phase 3 — Strategy B: Avellaneda & Lee (2010) PCA-Residual Mean Reversion.
Statistical arbitrage on Indian F&O equities.

Steps:
1. Rolling PCA on 252-day standardized returns matrix (k=5 factors default).
2. Regress each stock on top k factor returns -> idiosyncratic residuals.
3. Fit Ornstein-Uhlenbeck (OU) process to cumulative residuals on 60-day window.
4. Calculate s-score = (X_t - mu) / sigma_eq.
5. Trading rule:
   - Open long residual if s < -1.25 and kappa > kappa_min
   - Open short residual if s > +1.25 and kappa > kappa_min
   - Close long if s > -0.50
   - Close short if s < +0.75
6. Construct dollar-neutral portfolio capped at 10% notional per stock.
"""

import logging
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from pathlib import Path
import yaml

LOG = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

CONF_B = CFG.get("strategy_b", {})


def fit_pca_factors(returns_window: pd.DataFrame, k: int = 5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fits PCA on standardized returns over rolling window (e.g. 252 days).
    Returns:
      factor_returns: (T, k) array of principal component factor returns
      eigenvalues: top k explained variances
      components: (k, N) array of loadings
    """
    # Standardize returns cross-sectionally & time-series
    mean_r = returns_window.mean(axis=0)
    std_r = returns_window.std(axis=0).replace(0, 1e-6)
    r_norm = (returns_window - mean_r) / std_r

    pca = PCA(n_components=k)
    factors = pca.fit_transform(r_norm.values)
    return factors, pca.explained_variance_, pca.components_


def compute_residuals(returns_window: pd.DataFrame, factor_returns: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Regresses each stock's returns on the k factor returns:
    R_i = alpha_i + sum(beta_{i, j} * F_j) + eps_i
    Returns:
      residuals_df: DataFrame of daily idiosyncratic residuals eps_i
      betas: (N, k) array of regression betas
    """
    T, N = returns_window.shape
    k = factor_returns.shape[1]
    
    # Add constant for OLS regression
    X = np.column_stack([np.ones(T), factor_returns])
    Y = returns_window.values

    # OLS solution: (X'X)^(-1) X' Y
    betas_all, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
    # betas_all shape: (k+1, N). row 0 = alpha, rows 1..k = betas
    alphas = betas_all[0, :]
    betas = betas_all[1:, :].T  # shape (N, k)

    fitted = X @ betas_all
    residuals = Y - fitted
    residuals_df = pd.DataFrame(residuals, index=returns_window.index, columns=returns_window.columns)
    return residuals_df, betas


def fit_ou_process(cumulative_residual: np.ndarray, dt: float = 1.0 / 252.0) -> Tuple[float, float, float, float]:
    """
    Fits 1-D Ornstein-Uhlenbeck process on cumulative residual series:
    dX_t = kappa * (mu - X_t) dt + sigma * dW_t
    Discrete AR(1): X_{t+1} = a + b * X_t + eta_t
    where b = exp(-kappa * dt), a = mu * (1 - b)
    
    Returns:
      kappa: mean reversion speed (annualized)
      mu: long-term equilibrium mean
      sigma_eq: equilibrium standard deviation = sqrt(Var(eta) / (1 - b^2))
      half_life: half life in days = ln(2) / kappa
    """
    x = cumulative_residual
    if len(x) < 10:
        return 0.0, 0.0, 1e-4, 999.0

    x_lag = x[:-1]
    x_curr = x[1:]
    
    # Regression x_curr on x_lag
    n = len(x_lag)
    x_bar = np.mean(x_lag)
    y_bar = np.mean(x_curr)
    
    denom = np.sum((x_lag - x_bar) ** 2)
    if denom < 1e-12:
        return 0.0, 0.0, 1e-4, 999.0

    b = np.sum((x_lag - x_bar) * (x_curr - y_bar)) / denom
    a = y_bar - b * x_bar

    # Check for mean-reverting property (0 < b < 1)
    if b <= 0.0001 or b >= 0.9999:
        return 0.0, float(np.mean(x)), 1e-4, 999.0

    residuals = x_curr - (a + b * x_lag)
    var_eta = np.var(residuals, ddof=2) if len(residuals) > 2 else np.var(residuals)

    kappa = -np.log(b) / dt
    mu = a / (1.0 - b)
    
    # Equilibrium standard deviation
    denom_sig = 1.0 - b ** 2
    if denom_sig <= 0 or var_eta <= 0:
        return 0.0, float(mu), 1e-4, 999.0

    sigma_eq = np.sqrt(var_eta / denom_sig)
    half_life = np.log(2.0) / kappa * 252.0  # in trading days

    return float(kappa), float(mu), float(sigma_eq), float(half_life)


def compute_s_scores(
    residuals_df: pd.DataFrame,
    ou_window: int = 60,
    kappa_min: float = 0.003968
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Avellaneda-Lee s-score for each stock on the current day:
    s_i = (X_i(t) - mu_i) / sigma_eq_i
    Returns:
      s_scores: Series of s-scores indexed by symbol
      kappas: Series of mean-reversion speeds
      half_lives: Series of half-lives in days
    """
    # Cumulative residuals over window
    cum_res = residuals_df.tail(ou_window).cumsum()
    symbols = residuals_df.columns
    
    s_dict = {}
    k_dict = {}
    hl_dict = {}

    for sym in symbols:
        x_series = cum_res[sym].values
        kappa, mu, sig_eq, hl = fit_ou_process(x_series)
        
        if kappa >= kappa_min and sig_eq > 1e-6:
            # Dimensionless s-score centered around equilibrium
            s = (x_series[-1] - mu) / sig_eq
        else:
            s = 0.0  # does not meet mean-reversion criterion

        s_dict[sym] = s
        k_dict[sym] = kappa
        hl_dict[sym] = hl

    return pd.Series(s_dict), pd.Series(k_dict), pd.Series(hl_dict)


def generate_pca_ou_weights(
    s_scores: pd.Series,
    current_positions: pd.Series,
    s_open_long: float = -1.25,
    s_open_short: float = 1.25,
    s_close_long: float = -0.50,
    s_close_short: float = 0.75,
    max_weight: float = 0.10
) -> pd.Series:
    """
    Generates dollar-neutral portfolio target weights based on s-scores.
    Long signals: s < -1.25 (oversold residual)
    Short signals: s > +1.25 (overbought residual)
    Exit long: s > -0.50
    Exit short: s < +0.75
    """
    new_pos = current_positions.copy()

    for sym, s in s_scores.items():
        curr = new_pos.get(sym, 0.0)
        
        if curr == 0.0:
            if s <= s_open_long:
                new_pos[sym] = 1.0   # Open long
            elif s >= s_open_short:
                new_pos[sym] = -1.0  # Open short
        elif curr > 0:  # Currently long
            if s >= s_close_long:
                new_pos[sym] = 0.0   # Close long
        elif curr < 0:  # Currently short
            if s <= s_close_short:
                new_pos[sym] = 0.0   # Close short

    # Convert positions (-1, 0, 1) into dollar-neutral weights
    longs = new_pos[new_pos > 0].index
    shorts = new_pos[new_pos < 0].index

    weights = pd.Series(0.0, index=s_scores.index)
    if len(longs) > 0:
        w_long = min(1.0 / len(longs), max_weight)
        weights[longs] = w_long
    if len(shorts) > 0:
        w_short = min(1.0 / len(shorts), max_weight)
        weights[shorts] = -w_short

    # Enforce exact dollar neutrality
    sum_long = weights[weights > 0].sum()
    sum_short = np.abs(weights[weights < 0].sum())
    if sum_long > 0 and sum_short > 0:
        # Scale to equal notional long and short
        scale = min(sum_long, sum_short)
        weights[weights > 0] *= (scale / sum_long)
        weights[weights < 0] *= (scale / sum_short)

    return weights
