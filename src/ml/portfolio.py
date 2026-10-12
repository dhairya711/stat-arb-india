"""
src/ml/portfolio.py
Phase 3 — Strategy C: Portfolio construction from ML predictions.
Forms dollar-neutral quintile spread portfolios (Long Q5, Short Q1)
with 5% maximum per-stock weight cap.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

PORT_CONF = CFG.get("strategy_c", {}).get("portfolio", {})
MAX_WEIGHT = PORT_CONF.get("max_weight_per_stock", 0.05)


def construct_ml_portfolio_weights(
    predictions_df: pd.DataFrame,
    max_weight: float = MAX_WEIGHT
) -> pd.DataFrame:
    """
    Given out-of-sample predictions [trade_date, symbol, y_pred],
    ranks stocks cross-sectionally per date and assigns quintile weights:
      Long Q5 (highest expected return)
      Short Q1 (lowest expected return)
    Returns:
      weights_df: panel with [trade_date, symbol, weight]
    """
    df = predictions_df.copy()
    weights_list = []

    for d, group in df.groupby("trade_date"):
        n = len(group)
        if n < 5:
            continue
        
        # Cross-sectional rank into 5 quintiles (1 = bottom, 5 = top)
        group = group.copy()
        group["rank"] = pd.qcut(group["y_pred"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
        
        longs = group[group["rank"] == 5]
        shorts = group[group["rank"] == 1]
        
        n_l = len(longs)
        n_s = len(shorts)
        
        w_per_long = min(0.5 / n_l, max_weight) if n_l > 0 else 0.0
        w_per_short = min(0.5 / n_s, max_weight) if n_s > 0 else 0.0
        
        for _, row in group.iterrows():
            sym = row["symbol"]
            rk = row["rank"]
            if rk == 5:
                w = w_per_long
            elif rk == 1:
                w = -w_per_short
            else:
                w = 0.0
            weights_list.append({"trade_date": d, "symbol": sym, "weight": w})

    return pd.DataFrame(weights_list)


def compute_ml_portfolio_returns(
    weights_df: pd.DataFrame,
    returns_matrix: pd.DataFrame
) -> pd.Series:
    """
    Computes daily portfolio return = sum(w_{i, t} * R_{i, t+1}).
    weights_df: DataFrame with [trade_date, symbol, weight]
    returns_matrix: DataFrame indexed by date, columns = symbols
    """
    w_pivot = weights_df.pivot(index="trade_date", columns="symbol", values="weight").fillna(0.0)
    # Align dates
    common_dates = w_pivot.index.intersection(returns_matrix.index)
    w_aligned = w_pivot.loc[common_dates]
    r_aligned = returns_matrix.loc[common_dates]
    
    # Dot product row by row
    port_ret = (w_aligned * r_aligned).sum(axis=1)
    return port_ret
