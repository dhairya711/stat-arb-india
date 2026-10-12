"""
src/stats/regime.py
Phase 4 — Volatility Regime Analysis:
Partitions statistical arbitrage performance into volatility regimes:
High Volatility (top 30%), Normal Volatility (middle 40%), Low Volatility (bottom 30%)
using 22-day rolling realized market volatility.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from src.stats.subperiod import compute_performance_metrics


def analyze_volatility_regimes(
    strategy_returns: pd.Series,
    market_returns: pd.Series,
    rolling_window: int = 22
) -> pd.DataFrame:
    """
    Evaluates strategy performance across market volatility regimes.
    """
    common_idx = strategy_returns.index.intersection(market_returns.index)
    strat = strategy_returns.loc[common_idx]
    mkt = market_returns.loc[common_idx]

    # Realized rolling annualized volatility of market
    mkt_vol = mkt.rolling(rolling_window, min_periods=10).std() * np.sqrt(252.0)
    
    # Clean NaNs
    valid = ~(strat.isna() | mkt_vol.isna())
    strat_v = strat.loc[valid]
    vol_v = mkt_vol.loc[valid]

    q30 = vol_v.quantile(0.30)
    q70 = vol_v.quantile(0.70)

    low_vol_mask = vol_v <= q30
    mid_vol_mask = (vol_v > q30) & (vol_v < q70)
    high_vol_mask = vol_v >= q70

    regimes = {
        "Low Volatility (<=30th pct)": strat_v[low_vol_mask],
        "Normal Volatility (30th-70th pct)": strat_v[mid_vol_mask],
        "High Volatility (>=70th pct)": strat_v[high_vol_mask],
    }

    rows = []
    for reg_name, rets in regimes.items():
        m = compute_performance_metrics(rets)
        m["regime"] = reg_name
        rows.append(m)

    return pd.DataFrame(rows)
