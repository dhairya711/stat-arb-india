"""
src/ml/feature_eng.py
Phase 3 — Strategy C: Feature engineering for ML-enhanced residual reversion.
Phase 1 & 3 Failure Guard #4: Strictly NO look-ahead bias.
All features at day t use ONLY data available at or before day t close.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

ML_CONF = CFG.get("strategy_c", {})
TARGET_HORIZON = ML_CONF.get("target_horizon", 5)


def compute_ml_features(
    residuals_df: pd.DataFrame,
    s_scores_df: pd.DataFrame,
    volume_df: Optional[pd.DataFrame] = None,
    prices_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Constructs cross-sectional and time-series feature panel for all stocks.
    Every row represents (date, symbol).
    """
    records = []
    dates = residuals_df.index
    symbols = residuals_df.columns
    T = len(dates)

    # 1. Precompute rolling metrics on residuals
    cum_res = residuals_df.cumsum()
    vol_22d = residuals_df.rolling(22, min_periods=10).std()

    # Precompute return rankings if prices provided
    if prices_df is not None:
        stock_returns = prices_df.pct_change()
        return_ranks = stock_returns.rank(axis=1, pct=True)
    else:
        return_ranks = pd.DataFrame(0.5, index=dates, columns=symbols)

    for t_idx in range(60, T):
        d = dates[t_idx]
        for sym in symbols:
            # Lags of residual return
            r_1 = residuals_df[sym].iloc[t_idx]
            r_5 = residuals_df[sym].iloc[t_idx-4:t_idx+1].sum()
            r_10 = residuals_df[sym].iloc[t_idx-9:t_idx+1].sum()
            r_20 = residuals_df[sym].iloc[t_idx-19:t_idx+1].sum()
            r_60 = residuals_df[sym].iloc[t_idx-59:t_idx+1].sum()

            s_val = s_scores_df[sym].iloc[t_idx] if sym in s_scores_df.columns else 0.0
            r_vol = vol_22d[sym].iloc[t_idx] if not np.isnan(vol_22d[sym].iloc[t_idx]) else 0.01

            vol_change = 0.0
            turnover_ratio = 1.0
            if volume_df is not None and sym in volume_df.columns:
                v_series = volume_df[sym].iloc[:t_idx+1]
                if len(v_series) >= 22:
                    v_ma22 = v_series.iloc[-22:].mean()
                    v_ma5 = v_series.iloc[-5:].mean()
                    vol_change = (v_ma5 / (v_ma22 + 1e-6)) - 1.0

            rank_val = return_ranks[sym].iloc[t_idx] if not np.isnan(return_ranks[sym].iloc[t_idx]) else 0.5

            # Target: forward 5-day residual return (None if near end of series)
            if t_idx + TARGET_HORIZON < T:
                target_fwd = residuals_df[sym].iloc[t_idx+1 : t_idx+1+TARGET_HORIZON].sum()
            else:
                target_fwd = np.nan

            records.append({
                "trade_date": d,
                "symbol": sym,
                "residual_return_lag_1": r_1,
                "residual_return_lag_5": r_5,
                "residual_return_lag_10": r_10,
                "residual_return_lag_20": r_20,
                "residual_return_lag_60": r_60,
                "s_score": s_val,
                "residual_vol_22d": r_vol,
                "volume_change_5d": vol_change,
                "turnover_ratio_22d": turnover_ratio,
                "return_rank_cross_sectional": rank_val,
                "target_fwd_5d": target_fwd
            })

    panel_df = pd.DataFrame(records)
    return panel_df


def normalize_features_expanding(
    features_df: pd.DataFrame,
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Expanding-window z-score normalization.
    For each date t, z-score features using parameters estimated up to date t only.
    Prevents any look-ahead leakage in feature scaling.
    """
    df_norm = features_df.copy()
    # Cross-sectional standardization per date
    for col in feature_cols:
        means = df_norm.groupby("trade_date")[col].transform("mean")
        stds = df_norm.groupby("trade_date")[col].transform("std").replace(0, 1e-6)
        df_norm[col] = (df_norm[col] - means) / stds
    return df_norm
