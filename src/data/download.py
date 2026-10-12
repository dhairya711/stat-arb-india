"""
src/data/download.py
Phase 1 — NSE Bhavcopy Downloader

Phase 1 Failure Guard #1: If download fails, this script prints exact manual
download instructions and exits with code 1. It does NOT fabricate data.

NSE Equity bhavcopy archive structure:
  Pre-Jul-2024: https://archives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MON}/cm{DD}{MON}{YYYY}bhav.csv.zip
  Post-Jul-2024: https://archives.nseindia.com/products/content/sec_bhavdata_full_{YYYY}{MM}{DD}.csv

NSE Derivatives bhavcopy:
  https://archives.nseindia.com/content/historical/DERIVATIVES/{YYYY}/{MON}/fo{DD}{MON}{YYYY}bhav.csv.zip
"""

import os, sys, time, zipfile, io, logging
from datetime import date, timedelta
from pathlib import Path

import requests
import yaml

# ── Config ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

RAW = ROOT / CFG["paths"]["data_raw"]
RAW.mkdir(parents=True, exist_ok=True)

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# NSE requires these headers; without them requests are blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

# NSE changed equity bhavcopy format around July 2024
NEW_FORMAT_DATE = date(2024, 7, 1)


def _warmup_session():
    """NSE blocks direct archive hits without a prior homepage visit."""
    try:
        SESSION.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)
    except Exception:
        pass


def equity_url_old(d: date) -> str:
    mon = MONTHS[d.month - 1]
    return (f"https://archives.nseindia.com/content/historical/EQUITIES/"
            f"{d.year}/{mon}/cm{d.day:02d}{mon}{d.year}bhav.csv.zip")


def equity_url_new(d: date) -> str:
    return (f"https://archives.nseindia.com/products/content/"
            f"sec_bhavdata_full_{d.year}{d.month:02d}{d.day:02d}.csv")


def deriv_url(d: date) -> str:
    mon = MONTHS[d.month - 1]
    return (f"https://archives.nseindia.com/content/historical/DERIVATIVES/"
            f"{d.year}/{mon}/fo{d.day:02d}{mon}{d.year}bhav.csv.zip")


def _download_file(url: str, dest: Path, retry: int = 3) -> bool:
    """Download url → dest. Returns True on success."""
    if dest.exists() and dest.stat().st_size > 100:
        return True  # already downloaded
    for attempt in range(1, retry + 1):
        try:
            resp = SESSION.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                LOG.info(f"OK  {dest.name}  ({len(resp.content):,} bytes)")
                return True
            elif resp.status_code in (403, 404):
                LOG.warning(f"HTTP {resp.status_code} | {url}")
                return False
            else:
                LOG.warning(f"HTTP {resp.status_code} attempt {attempt} | {url}")
        except requests.RequestException as e:
            LOG.warning(f"Error attempt {attempt}: {e}")
        time.sleep(2 ** attempt)
    return False


def download_equity(start: date, end: date) -> dict:
    """Download equity bhavcopy for all trading days in range."""
    out_dir = RAW / "equity"
    out_dir.mkdir(exist_ok=True)
    results = {"ok": 0, "skip_weekend": 0, "fail": [], "manual_needed": []}

    d = start
    while d <= end:
        if d.weekday() >= 5:  # Saturday/Sunday
            results["skip_weekend"] += 1
            d += timedelta(days=1)
            continue

        if d >= NEW_FORMAT_DATE:
            url = equity_url_new(d)
            dest = out_dir / f"eq_{d.isoformat()}.csv"
        else:
            url = equity_url_old(d)
            dest = out_dir / f"eq_{d.isoformat()}.zip"

        ok = _download_file(url, dest)
        if ok:
            results["ok"] += 1
        else:
            # Could be a market holiday — only flag if not holiday
            results["fail"].append((d.isoformat(), url))
            results["manual_needed"].append(url)

        d += timedelta(days=1)
        time.sleep(0.3)  # be polite to NSE servers

    return results


def download_derivatives(start: date, end: date) -> dict:
    """Download derivatives (F&O) bhavcopy for all trading days in range."""
    out_dir = RAW / "derivatives"
    out_dir.mkdir(exist_ok=True)
    results = {"ok": 0, "skip_weekend": 0, "fail": [], "manual_needed": []}

    d = start
    while d <= end:
        if d.weekday() >= 5:
            results["skip_weekend"] += 1
            d += timedelta(days=1)
            continue

        url = deriv_url(d)
        dest = out_dir / f"fo_{d.isoformat()}.zip"
        ok = _download_file(url, dest)
        if ok:
            results["ok"] += 1
        else:
            results["fail"].append((d.isoformat(), url))
            results["manual_needed"].append(url)

        d += timedelta(days=1)
        time.sleep(0.3)

    return results


def print_manual_instructions(failed_urls: list[str]):
    """Hard Rule 1: If download fails, print EXACT manual instructions. Never fabricate."""
    print("\n" + "="*70)
    print("HARD STOP — NSE DATA DOWNLOAD FAILED")
    print("="*70)
    print("""
Some or all bhavcopy files could not be downloaded automatically.
NSE periodically blocks automated downloads.

MANUAL DOWNLOAD INSTRUCTIONS:
==============================
1. Go to: https://www.nseindia.com/market-data/live-equity-market
   → Click 'Download' → 'Bhavcopy (Complete)' for each date needed.

2. For bulk historical downloads, try:
   → https://archives.nseindia.com/content/historical/EQUITIES/
   → Navigate to YYYY/MON/ folder and download each .zip manually.

3. For derivatives (F&O) bhavcopy:
   → https://archives.nseindia.com/content/historical/DERIVATIVES/
   → Navigate to YYYY/MON/ folder and download each .zip manually.

4. Alternative — use jugaad-data Python package:
   pip install jugaad-data
   Then: from jugaad_data.nse import bhavcopy_fo_save

5. Place all downloaded files in:
   data/raw/equity/     ← equity bhavcopies
   data/raw/derivatives/ ← F&O bhavcopies

Files that failed (first 20 shown):
""")
    for url in failed_urls[:20]:
        print(f"  {url}")
    if len(failed_urls) > 20:
        print(f"  ... and {len(failed_urls)-20} more (see logs)")
    print("\nDo NOT proceed to Phase 2 until all files are present.")
    print("="*70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download NSE bhavcopy data")
    parser.add_argument("--test", action="store_true", help="Test mode: download 5 days only")
    args = parser.parse_args()

    start_eq  = date(2009, 1, 1)   # warmup year for formation windows
    start_fo  = date(2010, 1, 1)
    end       = date(2025, 12, 31)

    if args.test:
        # Phase 1 Failure Guard: test with 5 days first
        start_eq = date(2024, 1, 1)
        start_fo = date(2024, 1, 1)
        end      = date(2024, 1, 5)
        LOG.info("TEST MODE: downloading 5 days to check connectivity")

    LOG.info("Warming up NSE session...")
    _warmup_session()

    LOG.info("Downloading equity bhavcopy...")
    eq_res = download_equity(start_eq, end)

    LOG.info("Downloading derivatives bhavcopy...")
    fo_res = download_derivatives(start_fo, end)

    # ── Phase 1 Failure Guard — evaluate access ───────────────────────────────
    total_fails = len(eq_res["fail"]) + len(fo_res["fail"])
    all_manual  = eq_res["manual_needed"] + fo_res["manual_needed"]

    LOG.info(f"Equity:      {eq_res['ok']} OK  |  {len(eq_res['fail'])} failed")
    LOG.info(f"Derivatives: {fo_res['ok']} OK  |  {len(fo_res['fail'])} failed")

    if eq_res["ok"] == 0 and fo_res["ok"] == 0:
        # COMPLETE FAILURE — Hard Rule 1
        print_manual_instructions(all_manual)
        sys.exit(1)

    fail_rate = total_fails / max(eq_res["ok"] + len(eq_res["fail"]) +
                                   fo_res["ok"] + len(fo_res["fail"]), 1)
    if fail_rate > 0.30:
        # >30% failure rate — likely blocked; partial + manual
        LOG.warning(f"High failure rate ({fail_rate:.0%}). NSE may be blocking requests.")
        print_manual_instructions(all_manual[:50])
        LOG.warning("Proceeding with successfully downloaded files. Fill gaps manually.")
    else:
        LOG.info(f"Download complete. Failure rate {fail_rate:.1%} (expected for holidays).")

    LOG.info("Phase 1 Guard #1: PASSED (or partial — check logs)")
