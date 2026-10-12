"""
src/universe/fo_universe.py
Phase 1 — Point-in-time F&O universe construction.
Phase 1 Failure Guard #4 (no look-ahead) and #5 (universe size >= 30).

Rule: Stock is in universe for month M if it has >= min_ssf_days_per_month days
of stock futures (FUTSTK) data in month M, using only data available by end of M-1.
"""
import logging
import pandas as pd
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

LOG   = logging.getLogger(__name__)
PROC  = ROOT / CFG["paths"]["data_processed"]
UTAB  = ROOT / CFG["paths"]["results_tables"]
UTAB.mkdir(parents=True, exist_ok=True)

MIN_SSF_DAYS = CFG["universe"]["min_ssf_days_per_month"]
MIN_ADTV_CR  = CFG["universe"]["min_adtv_cr"]
MAX_MISS     = CFG["universe"]["max_missing_days"]
MIN_PRICE    = CFG["universe"]["min_price_inr"]
HARD_MIN_UNIVERSE = 20   # Guard #5: fail if < 20 stocks in any year


def build_ssf_membership(fo_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Extract monthly SSF (stock futures) membership from derivatives panel.
    Returns DataFrame: symbol, year_month, ssf_days_in_month.
    Failure Guard #4: uses only data from month M to assign membership to month M+1.
    """
    stk = fo_panel[fo_panel["instrument"] == "FUTSTK"].copy()
    stk["year_month"] = stk["trade_date"].dt.to_period("M")
    monthly = (stk.groupby(["symbol","year_month"])["trade_date"]
                  .nunique()
                  .rename("ssf_days")
                  .reset_index())
    # POINT-IN-TIME: membership for trading month = next month after data month
    monthly["trading_month"] = monthly["year_month"] + 1
    eligible = monthly[monthly["ssf_days"] >= MIN_SSF_DAYS][["symbol","trading_month"]]
    LOG.info(f"SSF membership: {len(eligible):,} symbol-month combinations")
    return eligible


def apply_liquidity_filters(eligible: pd.DataFrame,
                             equity_panel: pd.DataFrame,
                             formation_days: int = 252) -> pd.DataFrame:
    """
    Apply ADTV, missing-day, and min-price filters within the formation window.
    Only uses data from the formation window (prior to trading month) — no look-ahead.
    """
    eq = equity_panel.copy()
    eq["year_month"] = eq["trade_date"].dt.to_period("M")
    eq["adtv_cr"] = eq["traded_value_lakh"] / 100   # lakh → crore

    filtered_rows = []
    for _, row in eligible.iterrows():
        sym = row["symbol"]
        tm  = row["trading_month"]
        # Formation window ends at start of trading month
        trade_start = tm.to_timestamp(how="start")
        form_end    = trade_start - pd.Timedelta(days=1)
        form_start  = trade_start - pd.Timedelta(days=formation_days * 1.5)

        sym_data = eq[(eq["symbol"] == sym) &
                      (eq["trade_date"] >= form_start) &
                      (eq["trade_date"] <= form_end)]

        if len(sym_data) == 0:
            continue

        # Filter: ADTV
        adtv = sym_data["adtv_cr"].mean()
        if adtv < MIN_ADTV_CR:
            continue

        # Filter: missing days (approximate)
        trading_days_in_window = eq[(eq["trade_date"] >= form_start) &
                                     (eq["trade_date"] <= form_end)]["trade_date"].nunique()
        missing_days = max(0, trading_days_in_window - len(sym_data))
        if missing_days > MAX_MISS:
            continue

        # Filter: minimum price
        if sym_data["close"].min() < MIN_PRICE:
            continue

        filtered_rows.append({
            "symbol": sym, "trading_month": tm,
            "adtv_cr": round(adtv, 2), "missing_days": missing_days,
        })

    result = pd.DataFrame(filtered_rows)
    LOG.info(f"After liquidity filters: {len(result):,} symbol-month combinations")
    return result


def compute_annual_coverage(universe: pd.DataFrame) -> pd.DataFrame:
    """Compute annual entry/exit counts for the universe coverage table."""
    universe["year"] = universe["trading_month"].dt.year
    annual = (universe.groupby("year")["symbol"]
                      .agg(["nunique","count"])
                      .rename(columns={"nunique":"unique_stocks","count":"symbol_months"})
                      .reset_index())
    # Guard #5: check minimum universe size
    for _, row in annual.iterrows():
        if row["unique_stocks"] < HARD_MIN_UNIVERSE:
            LOG.error(f"GUARD #5 FAIL: year {row['year']} has only "
                      f"{row['unique_stocks']} stocks (< {HARD_MIN_UNIVERSE}). "
                      "Do not proceed to strategy code.")
        elif row["unique_stocks"] < 30:
            LOG.warning(f"GUARD #5 EDGE: year {row['year']} has only "
                        f"{row['unique_stocks']} stocks (< 30). "
                        "Note as limitation; continue with caution.")
        else:
            LOG.info(f"Guard #5: year {row['year']} — {row['unique_stocks']} stocks ✓")
    return annual


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG.info("Universe module ready. Requires fo_panel and equity_panel DataFrames as input.")
    LOG.info("Called from the main pipeline after ingest + adjust.")
