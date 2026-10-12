"""
src/ml/walk_forward.py
Phase 3 — Strategy C: Walk-forward expanding-window validation.
Phase 3 Failure Guard #4: Embargo gap strictly prevents target leakage into test period.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import yaml
from src.ml.models import get_ml_model

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

ML_CONF = CFG.get("strategy_c", {})
WF_CONF = ML_CONF.get("walk_forward", {})
FEATURE_COLS = ML_CONF.get("features", [])


def run_walk_forward_predictions(
    features_df: pd.DataFrame,
    model_name: str = "ridge",
    embargo_days: int = 10,
    oos_start_year: int = 2016,
    end_year: int = 2025
) -> pd.DataFrame:
    """
    Executes expanding-window walk-forward validation.
    For each test year Y:
      Train: all data with trade_date.year < Y (minus embargo buffer at the end)
      Test: trade_date.year == Y
    Returns:
      DataFrame of out-of-sample predictions with columns [trade_date, symbol, y_true, y_pred]
    """
    df = features_df.dropna(subset=FEATURE_COLS).copy()
    df["year"] = pd.to_datetime(df["trade_date"]).dt.year

    all_oos_records = []

    for test_yr in range(oos_start_year, end_year + 1):
        # Training data: prior years
        train_mask = df["year"] < test_yr
        train_data = df[train_mask]

        if len(train_data) < 100:
            continue

        # Embargo buffer: drop the last `embargo_days` of training data to prevent overlap with forward targets
        train_dates = sorted(train_data["trade_date"].unique())
        if len(train_dates) > embargo_days:
            embargo_cutoff = train_dates[-embargo_days]
            train_data = train_data[train_data["trade_date"] < embargo_cutoff]

        # Valid train rows with target
        train_valid = train_data.dropna(subset=["target_fwd_5d"])
        X_train = train_valid[FEATURE_COLS].values
        y_train = train_valid["target_fwd_5d"].values

        # Test data for year test_yr
        test_data = df[df["year"] == test_yr].copy()
        if len(test_data) == 0:
            continue

        X_test = test_data[FEATURE_COLS].values

        # Train model
        model = get_ml_model(model_name)
        model.fit(X_train, y_train)

        # Predict out of sample
        preds = model.predict(X_test)
        test_data["y_pred"] = preds

        all_oos_records.append(test_data[["trade_date", "symbol", "target_fwd_5d", "y_pred"]])

    if not all_oos_records:
        return pd.DataFrame(columns=["trade_date", "symbol", "target_fwd_5d", "y_pred"])

    return pd.concat(all_oos_records, ignore_index=True)
