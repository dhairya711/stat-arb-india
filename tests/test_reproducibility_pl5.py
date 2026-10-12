"""
tests/test_reproducibility_pl5.py
Placebo Test PL5: Pipeline Determinism and Bitwise Reproducibility.
Verifies that identical seed and inputs produce bitwise-identical results across multiple runs.
Hard Fail: Two separate runs produce different cryptographic hashes.
"""

import hashlib
import numpy as np
import pandas as pd
from src.strategies.gatev import simulate_pair_trading


def generate_run_hash(seed: int = 42) -> str:
    np.random.seed(seed)
    n_days = 200
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")
    rw = np.cumsum(np.random.normal(0, 0.01, n_days)) + 100.0
    spread = np.zeros(n_days)
    for t in range(1, n_days):
        spread[t] = 0.75 * spread[t-1] + np.random.normal(0, 1.0)
    
    p_a = pd.Series(rw + spread, index=dates)
    p_b = pd.Series(rw, index=dates)

    rets, trades = simulate_pair_trading(p_a, p_b, spread_std=1.0, entry_sigma=2.0)
    
    # Serialize returns to bytes
    hasher = hashlib.sha256()
    hasher.update(rets.values.tobytes())
    return hasher.hexdigest()


def test_bitwise_reproducibility_pl5():
    hash_1 = generate_run_hash(seed=42)
    hash_2 = generate_run_hash(seed=42)

    assert hash_1 == hash_2, (
        f"PL5 HARD FAIL: Non-deterministic execution detected! "
        f"Hash 1: {hash_1} != Hash 2: {hash_2}"
    )
