"""
src/data/ingest.py
Phase 1 — Parse both old and new NSE bhavcopy formats into unified DataFrames.

Phase 1 Failure Guard #2: Both pre-2024 and post-Jul-2024 formats must parse
without errors. If either fails, an informative exception is raised.

Old equity format (pre Jul-2024): CSV inside ZIP
  Columns: SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN
New equity format (post Jul-2024): plain CSV (no zip)
  Columns differ — mapped explicitly below.

Derivatives format (unchanged): CSV inside ZIP
  Columns: INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,SETTLE_PR,
           CONTRACTS,VAL_INLAKH,OPEN_INT,CHG_IN_OI,TIMESTAMP
"""

import io, zipfile, logging
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT  = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

RAW   = ROOT / CFG["paths"]["data_raw"]
LOG   = logging.getLogger(__name__)
NEW_FORMAT_DATE = date(2024, 7, 1)

# ── Column maps ───────────────────────────────────────────────────────────────
EQ_OLD_COLS = {
    "SYMBOL": "symbol", "SERIES": "series", "OPEN": "open", "HIGH": "high",
    "LOW": "low", "CLOSE": "close", "PREVCLOSE": "prev_close",
    "TOTTRDQTY": "volume", "TOTTRDVAL": "traded_value_lakh", "TIMESTAMP": "date",
    "ISIN": "isin",
}
EQ_NEW_COLS = {
    # New format header (verify after first download — may need adjustment)
    "SYMBOL": "symbol", "SERIES": "series", "OPEN_PRICE": "open",
    "HIGH_PRICE": "high", "LOW_PRICE": "low", "CLOSE_PRICE": "close",
    "PREV_CLOSE": "prev_close", "TTL_TRD_QNTY": "volume",
    "TURNOVER_LACS": "traded_value_lakh", "DATE1": "date", "ISIN_CODE": "isin",
}
FO_COLS = {
    "INSTRUMENT": "instrument", "SYMBOL": "symbol", "EXPIRY_DT": "expiry_date",
    "STRIKE_PR": "strike_price", "OPTION_TYP": "option_type", "OPEN": "open",
    "HIGH": "high", "LOW": "low", "CLOSE": "close", "SETTLE_PR": "settle_price",
    "CONTRACTS": "contracts", "VAL_INLAKH": "value_lakh",
    "OPEN_INT": "open_interest", "TIMESTAMP": "date",
}


def parse_equity_zip(path: Path, trade_date: date) -> pd.DataFrame:
    """Parse old-format equity bhavcopy (ZIP containing CSV)."""
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        df = pd.read_csv(zf.open(name), parse_dates=False)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={c: EQ_OLD_COLS[c] for c in df.columns if c in EQ_OLD_COLS})
    df["trade_date"] = pd.Timestamp(trade_date)
    df["format"] = "old"
    return _clean_equity(df[df["series"].isin(["EQ", "BE", "BZ"])])


def parse_equity_csv(path: Path, trade_date: date) -> pd.DataFrame:
    """Parse new-format equity bhavcopy (plain CSV, post Jul-2024)."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # Try new column names; fall back to old if headers match old format
    if "CLOSE_PRICE" in df.columns:
        df = df.rename(columns={c: EQ_NEW_COLS[c] for c in df.columns if c in EQ_NEW_COLS})
    elif "CLOSE" in df.columns:
        df = df.rename(columns={c: EQ_OLD_COLS[c] for c in df.columns if c in EQ_OLD_COLS})
    else:
        raise ValueError(f"Unrecognised equity CSV columns: {list(df.columns)[:5]}")
    df["trade_date"] = pd.Timestamp(trade_date)
    df["format"] = "new"
    return _clean_equity(df[df["series"].isin(["EQ", "BE", "BZ"])])


def parse_derivatives_zip(path: Path, trade_date: date) -> pd.DataFrame:
    """Parse derivatives (F&O) bhavcopy ZIP."""
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        df = pd.read_csv(zf.open(name), parse_dates=False)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={c: FO_COLS[c] for c in df.columns if c in FO_COLS})
    df["trade_date"] = pd.Timestamp(trade_date)
    return df


def _clean_equity(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["open", "high", "low", "close", "prev_close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    if "traded_value_lakh" in df.columns:
        df["traded_value_lakh"] = pd.to_numeric(df["traded_value_lakh"], errors="coerce")
    return df.dropna(subset=["close"])


def load_equity_day(trade_date: date) -> pd.DataFrame | None:
    """Load one equity bhavcopy day. Returns None if file not found."""
    eq_dir = RAW / "equity"
    if trade_date >= NEW_FORMAT_DATE:
        path = eq_dir / f"eq_{trade_date.isoformat()}.csv"
        if not path.exists(): return None
        return parse_equity_csv(path, trade_date)
    else:
        path = eq_dir / f"eq_{trade_date.isoformat()}.zip"
        if not path.exists(): return None
        return parse_equity_zip(path, trade_date)


def load_derivatives_day(trade_date: date) -> pd.DataFrame | None:
    """Load one derivatives bhavcopy day."""
    path = RAW / "derivatives" / f"fo_{trade_date.isoformat()}.zip"
    if not path.exists(): return None
    return parse_derivatives_zip(path, trade_date)


def build_equity_panel(start: date, end: date) -> pd.DataFrame:
    """Stack all equity bhavcopy days into one panel DataFrame."""
    frames = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            df = load_equity_day(d)
            if df is not None and len(df) > 0:
                frames.append(df)
        d += pd.Timedelta(days=1)
    if not frames:
        raise RuntimeError("No equity data found. Run download.py first.")
    panel = pd.concat(frames, ignore_index=True)
    LOG.info(f"Equity panel: {len(panel):,} rows, {panel['symbol'].nunique()} symbols, "
             f"{panel['trade_date'].nunique()} trading days")
    return panel


def build_derivatives_panel(start: date, end: date) -> pd.DataFrame:
    """Stack all derivatives bhavcopy days into one panel DataFrame."""
    frames = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            df = load_derivatives_day(d)
            if df is not None and len(df) > 0:
                frames.append(df)
        d += pd.Timedelta(days=1)
    if not frames:
        raise RuntimeError("No derivatives data found. Run download.py first.")
    panel = pd.concat(frames, ignore_index=True)
    LOG.info(f"Derivatives panel: {len(panel):,} rows, {panel['symbol'].nunique()} symbols")
    return panel


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    from datetime import date

    # Phase 1 Guard #2: test both formats
    test_cases = [
        date(2024, 1, 2),  # old format equity
        date(2024, 8, 1),  # new format equity (post Jul 2024)
    ]
    for d in test_cases:
        df = load_equity_day(d)
        if df is not None:
            LOG.info(f"Format guard {d}: OK — {len(df)} rows, cols: {list(df.columns)[:5]}")
        else:
            LOG.warning(f"Format guard {d}: File not found (download it first)")

    LOG.info("Phase 1 Guard #2 (format coverage): check logs above.")
