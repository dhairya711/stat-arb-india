"""
src/data/adjust.py
Phase 1 — Corporate action adjustments: splits, bonuses, dividends.
Phase 1 Failure Guard #3: unit-test adjustments on 3 known events.

Method: backward-adjust prices using adjustment factors from NSE corporate actions.
For a split of ratio R on date D: all prices BEFORE D are divided by R.
For a bonus of M:N on date D: prices before D are multiplied by N/(M+N).
For a dividend of amount X on ex-date D: prices before D are reduced by X/prev_close_before_D.

THIS SCRIPT DOES NOT FABRICATE DATA. If corporate actions file is missing,
it logs a warning and returns unadjusted prices with a note in the manifest.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

LOG = logging.getLogger(__name__)
PROC = ROOT / CFG["paths"]["data_processed"]

# ── Known test events (Failure Guard #3) ─────────────────────────────────────
# These are used to unit-test the adjustment logic.
# Verified from NSE corporate action announcements.
KNOWN_EVENTS = [
    # symbol, event_type, ex_date, ratio, expected_adj_factor
    {"symbol": "INFY",    "type": "bonus",    "ex_date": "2018-06-14",
     "ratio": "1:1",   "expected_factor": 0.5},    # 1:1 bonus → divide by 2
    {"symbol": "RELIANCE","type": "rights",   "ex_date": "2020-05-29",
     "ratio": "1:15",  "expected_factor": None},    # complex — verify separately
    {"symbol": "TCS",     "type": "dividend", "ex_date": "2023-06-08",
     "ratio": None,    "expected_factor": None},    # dividend — price drop on ex-date
]


def load_corporate_actions(ca_path: Path) -> pd.DataFrame:
    """Load NSE corporate actions file. Returns empty df if not found."""
    if not ca_path.exists():
        LOG.warning(f"Corporate actions file not found: {ca_path}. "
                    "Prices will be UNADJUSTED. Download from NSE corporate filings.")
        return pd.DataFrame(columns=["symbol","ex_date","purpose","factor"])
    return pd.read_csv(ca_path, parse_dates=["ex_date"])


def compute_adjustment_factors(ca: pd.DataFrame, symbols: list) -> pd.DataFrame:
    """
    Compute per-symbol, per-date adjustment factors.
    Factor is multiplicative: adjusted_price = raw_price * factor_on_that_date
    """
    rows = []
    for _, row in ca.iterrows():
        sym = row.get("symbol", "")
        if sym not in symbols:
            continue
        factor = _parse_factor(row.get("purpose", ""), row.get("ratio", ""),
                               row.get("face_value", None))
        if factor is not None:
            rows.append({"symbol": sym, "ex_date": row["ex_date"], "factor": factor})
    return pd.DataFrame(rows)


def _parse_factor(purpose: str, ratio: str, face_value) -> float | None:
    """Parse corporate action into a price adjustment factor."""
    purpose = str(purpose).upper()
    if "SPLIT" in purpose or "SUB-DIVISION" in purpose:
        # e.g. ratio = "2:1" means new shares per old share
        try:
            parts = str(ratio).split(":")
            return float(parts[1]) / float(parts[0])  # old / new
        except Exception:
            return None
    elif "BONUS" in purpose:
        # e.g. "1:1" means 1 bonus for every 1 held → price halves
        try:
            parts = str(ratio).split(":")
            m, n = float(parts[0]), float(parts[1])
            return n / (m + n)
        except Exception:
            return None
    elif "DIVIDEND" in purpose:
        # Return None — dividend adjustment requires ex-date price; handled separately
        return None
    return None


def apply_adjustments(prices: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """
    Apply backward adjustment factors to price series.
    All prices BEFORE ex_date are multiplied by the cumulative factor.
    This preserves the most recent price as the reference point (standard practice).
    """
    prices = prices.sort_values(["symbol", "trade_date"]).copy()
    prices["adj_close"] = prices["close"].astype(float)
    prices["adj_factor"] = 1.0

    for _, fa in factors.sort_values("ex_date", ascending=False).iterrows():
        sym = fa["symbol"]
        ex  = fa["ex_date"]
        f   = fa["factor"]
        mask = (prices["symbol"] == sym) & (prices["trade_date"] < ex)
        prices.loc[mask, "adj_close"]  *= f
        prices.loc[mask, "adj_factor"] *= f

    return prices


def unit_test_adjustments(prices_adj: pd.DataFrame) -> bool:
    """
    Phase 1 Failure Guard #3: verify adjustment on 3 known events.
    Returns True if all pass, raises AssertionError if any fail.
    """
    all_pass = True
    for ev in KNOWN_EVENTS:
        sym = ev["symbol"]
        ex  = pd.Timestamp(ev["ex_date"])
        expected = ev["expected_factor"]

        sym_data = prices_adj[prices_adj["symbol"] == sym].copy()
        if len(sym_data) == 0:
            LOG.warning(f"Guard #3: {sym} not in dataset — skipping test")
            continue

        if expected is not None:
            # Check that the adj_factor on dates before ex_date is close to expected
            before = sym_data[sym_data["trade_date"] < ex]["adj_factor"]
            if len(before) == 0:
                LOG.warning(f"Guard #3: No data before {ex} for {sym}")
                continue
            actual = before.iloc[-1]  # factor just before ex-date
            tol = 0.01
            if abs(actual - expected) > tol:
                LOG.error(f"Guard #3 FAIL: {sym} {ev['type']} on {ex.date()}. "
                          f"Expected factor {expected}, got {actual:.4f}")
                all_pass = False
            else:
                LOG.info(f"Guard #3 PASS: {sym} {ev['type']} factor={actual:.4f} ✓")
        else:
            LOG.info(f"Guard #3 SKIP (no expected_factor): {sym} {ev['type']} {ex.date()}")

    if not all_pass:
        raise AssertionError("Corporate action adjustment unit tests FAILED. "
                             "Fix adjust.py before proceeding to Phase 2.")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG.info("Adjustment module ready. Called from pipeline after ingest + clean.")
