"""
src/stats/subperiod.py
Phase 4 — Sub-period and Crash Episode Analysis:
Evaluates strategy resilience across pre-registered market epochs:
SP1 (2010-2014), SP2 (2015-2019), SP3 (2020-2025)
and stress periods (COVID crash, Demonetisation, 2022 selloff, post-SEBI 2024 reform).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import yaml
from src.stats.inference import newey_west_tstat

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

SUB_PERIODS = CFG.get("sub_periods", {})
CRASH_EPISODES = CFG.get("crash_episodes", {})


def compute_performance_metrics(daily_returns: pd.Series) -> Dict[str, float]:
    """Computes standard institutional performance metrics."""
    r = daily_returns.dropna()
    if len(r) < 5:
        return {
            "n_days": len(r), "return_ann": 0.0, "vol_ann": 0.0,
            "sharpe": 0.0, "max_drawdown": 0.0, "t_stat": 0.0, "p_val": 1.0
        }

    mean_d = r.mean()
    std_d = r.std()
    ret_ann = mean_d * 252.0
    vol_ann = std_d * np.sqrt(252.0) if std_d > 0 else 1e-6
    sharpe = ret_ann / vol_ann

    # Max Drawdown
    cum = (1.0 + r).cumprod()
    peak = cum.cummax()
    dd = (cum - peak) / peak
    max_dd = float(dd.min())

    t_stat, p_val, _ = newey_west_tstat(r)

    return {
        "n_days": len(r),
        "return_ann": float(ret_ann),
        "vol_ann": float(vol_ann),
        "sharpe": float(sharpe),
        "max_drawdown": max_dd,
        "t_stat": t_stat,
        "p_val": p_val
    }


def analyze_subperiods(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates returns across SP1, SP2, SP3.
    returns_df: indexed by DatetimeIndex, columns = strategy names
    """
    rows = []
    for sp_name, (start_d, end_d) in SUB_PERIODS.items():
        mask = (returns_df.index >= pd.Timestamp(start_d)) & (returns_df.index <= pd.Timestamp(end_d))
        sub_df = returns_df.loc[mask]
        for col in sub_df.columns:
            m = compute_performance_metrics(sub_df[col])
            m["subperiod"] = sp_name
            m["strategy"] = col
            m["start_date"] = start_d
            m["end_date"] = end_d
            rows.append(m)
    return pd.DataFrame(rows)


def analyze_crash_episodes(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates returns across pre-registered stress episodes.
    """
    rows = []
    for crash_name, (start_d, end_d) in CRASH_EPISODES.items():
        mask = (returns_df.index >= pd.Timestamp(start_d)) & (returns_df.index <= pd.Timestamp(end_d))
        sub_df = returns_df.loc[mask]
        for col in sub_df.columns:
            m = compute_performance_metrics(sub_df[col])
            m["episode"] = crash_name
            m["strategy"] = col
            m["start_date"] = start_d
            m["end_date"] = end_d
            rows.append(m)
    return pd.DataFrame(rows)
