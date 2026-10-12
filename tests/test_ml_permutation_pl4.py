"""
tests/test_ml_permutation_pl4.py
Placebo Test PL4: Target Permutation Placebo Test.
Verifies that the ML model does not produce spurious out-of-sample performance when targets are permuted.
Hard Fail: Permuted predictions give annualized out-of-sample Sharpe > 0.30.
"""

import numpy as np
import pandas as pd
from src.ml.models import RidgeModel


def test_ml_target_permutation_pl4():
    np.random.seed(42)
    n_samples = 1000
    n_features = 10

    # Generate synthetic features
    X = np.random.normal(0, 1, (n_samples, n_features))
    y = np.random.normal(0, 0.02, n_samples)

    # 1. Permute targets completely (break any true relationship)
    y_permuted = np.random.permutation(y)

    # Split into train and test
    split = 600
    X_train, y_train = X[:split], y_permuted[:split]
    X_test, y_test = X[split:], y[split:]

    # Train model on permuted targets
    model = RidgeModel()
    model.fit(X_train, y_train)

    # Out-of-sample predictions
    preds = model.predict(X_test)

    # Strategy: Long top 30%, Short bottom 30%
    threshold_top = np.percentile(preds, 70)
    threshold_bot = np.percentile(preds, 30)

    long_mask = preds >= threshold_top
    short_mask = preds <= threshold_bot

    oos_returns = np.zeros(len(y_test))
    oos_returns[long_mask] = y_test[long_mask]
    oos_returns[short_mask] = -y_test[short_mask]

    active_rets = oos_returns[long_mask | short_mask]
    if len(active_rets) > 10 and np.std(active_rets) > 0:
        daily_sharpe = np.mean(active_rets) / np.std(active_rets)
        ann_sharpe = daily_sharpe * np.sqrt(252)
    else:
        ann_sharpe = 0.0

    # PL4 Hard Fail Criterion: Sharpe must be <= 0.30
    assert ann_sharpe <= 0.30, (
        f"PL4 HARD FAIL: ML model produced spurious Sharpe = {ann_sharpe:.4f} > 0.30 "
        f"on completely permuted targets! Check for data snooping or target memorization."
    )
