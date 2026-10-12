from typing import Dict, List, Tuple, Optional
﻿"""
src/ml/ml_strategy.py
Phase 3 & 4 — Strategy C: End-to-end ML pipeline runner.
Integrates feature engineering, expanding-window walk-forward validation,
and dollar-neutral portfolio construction.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import yaml
import logging

from src.ml.feature_eng import compute_ml_features, normalize_features_expanding
from src.ml.walk_forward import run_walk_forward_predictions
from src.ml.portfolio import construct_ml_portfolio_weights, compute_ml_portfolio_returns

LOG = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

ML_CONF = CFG.get("strategy_c", {})
FEATURE_COLS = ML_CONF.get("features", [])


def run_ml_strategy_pipeline(
    residuals_df: pd.DataFrame,
    s_scores_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    volume_df: Optional[pd.DataFrame] = None,
    model_name: str = "ridge"
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """
    Executes end-to-end ML strategy.
    Returns:
      daily_returns: pd.Series of out-of-sample portfolio returns
      weights_df: out-of-sample portfolio weights panel
      predictions_df: out-of-sample predictions panel
    """
    LOG.info(f"Computing ML features for {model_name}...")
    panel = compute_ml_features(residuals_df, s_scores_df, volume_df=volume_df, prices_df=prices_df)
    
    LOG.info("Normalizing features expanding-window...")
    panel_norm = normalize_features_expanding(panel, FEATURE_COLS)

    LOG.info("Running walk-forward model training & prediction...")
    preds = run_walk_forward_predictions(panel_norm, model_name=model_name)

    if len(preds) == 0:
        return pd.Series(dtype=float), pd.DataFrame(), pd.DataFrame()

    LOG.info("Constructing dollar-neutral portfolio weights...")
    weights = construct_ml_portfolio_weights(preds)

    stock_returns = prices_df.pct_change()
    daily_rets = compute_ml_portfolio_returns(weights, stock_returns)

    return daily_rets, weights, preds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG.info("ML Strategy module compiled and ready.")
