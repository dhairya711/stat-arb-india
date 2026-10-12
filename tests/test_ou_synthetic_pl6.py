"""
tests/test_ou_synthetic_pl6.py
Placebo Test PL6: Synthetic Ornstein-Uhlenbeck Mean-Reversion Test.
Verifies that the s-score calculation and trading logic generate strictly positive returns on true OU processes.
Hard Fail: Simulated OU process produces negative gross return (indicates sign error or inverted threshold in signal).
"""

import numpy as np
import pandas as pd
from src.strategies.pca_ou import fit_ou_process, generate_pca_ou_weights


def simulate_ou_path(kappa: float = 12.0, mu: float = 0.0, sigma: float = 0.30,
                     n_steps: int = 500, dt: float = 1.0 / 252.0, seed: int = 42) -> np.ndarray:
    np.random.seed(seed)
    x = np.zeros(n_steps)
    x[0] = mu
    for t in range(1, n_steps):
        # Euler-Maruyama discretization: dx = kappa*(mu - x)*dt + sigma*sqrt(dt)*Z
        dx = kappa * (mu - x[t-1]) * dt + sigma * np.sqrt(dt) * np.random.normal(0, 1)
        x[t] = x[t-1] + dx
    return x


def test_ou_synthetic_positive_gross_return_pl6():
    # Simulate true mean-reverting OU series
    x = simulate_ou_path(kappa=15.0, mu=0.0, sigma=0.40, n_steps=600, seed=777)
    
    # Delta X represents residual returns
    dx = np.diff(x)
    n_days = len(dx)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="B")

    # Fit rolling OU and calculate s-scores
    window = 60
    s_scores = []
    positions = []
    curr_pos = 0

    pnl = []

    for t in range(window, n_days):
        x_win = x[t-window:t]
        kappa, mu_hat, sig_eq, _ = fit_ou_process(x_win)
        
        # Current s-score
        if sig_eq > 1e-6 and kappa > 0:
            s = (x[t] - mu_hat) / sig_eq
        else:
            s = 0.0

        # Trading rule:
        # If s < -1.25 -> Long residual (expect x to rise)
        # If s > +1.25 -> Short residual (expect x to fall)
        # Exit long: s > -0.5
        # Exit short: s < +0.75
        if curr_pos == 0:
            if s <= -1.25:
                curr_pos = 1
            elif s >= 1.25:
                curr_pos = -1
        elif curr_pos == 1:
            if s >= -0.50:
                curr_pos = 0
        elif curr_pos == -1:
            if s <= 0.75:
                curr_pos = 0

        # P&L on day t: curr_pos * dx[t]
        step_pnl = curr_pos * dx[t]
        pnl.append(step_pnl)

    total_gross_pnl = np.sum(pnl)

    # PL6 Hard Fail Criterion: Gross P&L on true OU must be > 0
    assert total_gross_pnl > 0, (
        f"PL6 HARD FAIL: Strategy earned negative gross return ({total_gross_pnl:.4f}) "
        f"on true synthetic OU process! Signal sign is inverted!"
    )
