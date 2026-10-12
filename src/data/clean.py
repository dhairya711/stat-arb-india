"""
src/data/clean.py
Phase 1 — Data cleaning: outlier detection, missing days, zero prices.
Phase 1 Failure Guard #4 (no look-ahead) and #6 (missing data) enforced here.
"""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

LOG = logging.getLogger(__name__)
PROC = ROOT / CFG["paths"]["data_processed"]
PROC.mkdir(parents=True, exist_ok=True)

OUTLIER_THRESHOLD = 0.40   # daily return > 40% flagged
MIN_PRICE = CFG["universe"]["min_price_inr"]


def clean_equity_panel(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean equity panel. Returns (clean_df, flags_df).
    Failure Guard #4: sort by trade_date ascending to ensure no look-ahead in indexing.
    Failure Guard #6: report missing day stats per symbol.
    """
    df = df.sort_values(["symbol", "trade_date"]).copy()

    # ── Compute daily returns (within each symbol, by trade_date order) ───────
    # Failure Guard #4: shift(1) gives YESTERDAY's close, not tomorrow's
    df["daily_return"] = df.groupby("symbol")["close"].pct_change()

    # ── Flag outliers ──────────────────────────────────────────────────────────
    flags = []
    outlier_mask = df["daily_return"].abs() > OUTLIER_THRESHOLD
    if outlier_mask.any():
        outliers = df[outlier_mask][["symbol","trade_date","close","daily_return"]].copy()
        outliers["flag"] = "outlier_return"
        flags.append(outliers)
        LOG.warning(f"Outlier returns flagged: {outlier_mask.sum()} rows "
                    f"({outlier_mask.mean():.3%} of data)")

    # ── Flag zero/negative prices ──────────────────────────────────────────────
    zero_mask = df["close"] <= 0
    if zero_mask.any():
        zeros = df[zero_mask][["symbol","trade_date","close"]].copy()
        zeros["flag"] = "zero_price"
        flags.append(zeros)
        LOG.warning(f"Zero/negative prices: {zero_mask.sum()} rows")
        # Carry forward previous price (do not fabricate; document)
        df.loc[zero_mask, "close"] = np.nan
        df["close"] = df.groupby("symbol")["close"].ffill()

    # ── Flag below minimum price ───────────────────────────────────────────────
    low_mask = df["close"] < MIN_PRICE
    if low_mask.any():
        low = df[low_mask][["symbol","trade_date","close"]].copy()
        low["flag"] = "below_min_price"
        flags.append(low)

    flags_df = pd.concat(flags, ignore_index=True) if flags else pd.DataFrame()

    # ── Missing day report (Guard #6) ─────────────────────────────────────────
    trading_days = df["trade_date"].nunique()
    missing_summary = (df.groupby("symbol")["trade_date"].count()
                         .rsub(trading_days)
                         .rename("missing_days")
                         .reset_index())
    high_miss = missing_summary[
        missing_summary["missing_days"] > CFG["universe"]["max_missing_days"]
    ]
    if len(high_miss) > 0:
        LOG.warning(f"Guard #6: {len(high_miss)} symbols exceed max_missing_days="
                    f"{CFG['universe']['max_missing_days']}")

    missing_summary.to_csv(PROC / "missing_days_by_symbol.csv", index=False)
    LOG.info(f"Cleaned equity panel: {len(df):,} rows. Flags: {len(flags_df)}")
    return df, flags_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG.info("Run via pipeline: python src/data/clean.py is called after ingest.")
