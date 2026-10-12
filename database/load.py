"""
database/load.py
Phase 1 — Load processed data into DuckDB database.
Executes schema.sql, populates tables from processed CSV/Parquet files,
and provides query execution helpers for analytics and Power BI export.
"""

import logging
from pathlib import Path
import duckdb
import yaml

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

DB_PATH = ROOT / "database" / "stat_arb.duckdb"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
QUERIES_DIR = ROOT / "database" / "queries"


def get_connection(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Returns a DuckDB connection to the local database file."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_schema(conn: duckdb.DuckDBPyConnection = None) -> None:
    """Executes schema.sql to create all tables."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    conn.execute(sql)
    LOG.info(f"Schema initialized successfully from {SCHEMA_PATH.name}")

    if close_after:
        conn.close()


def load_table_from_parquet_or_csv(table_name: str, file_path: Path, conn: duckdb.DuckDBPyConnection = None) -> int:
    """Inserts records from CSV or Parquet into table_name."""
    if not file_path.exists():
        LOG.warning(f"File {file_path} not found. Skipping table {table_name}.")
        return 0

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        if str(file_path).endswith(".parquet"):
            conn.execute(f"INSERT OR REPLACE INTO {table_name} SELECT * FROM read_parquet('{file_path.as_posix()}')")
        else:
            conn.execute(f"INSERT OR REPLACE INTO {table_name} SELECT * FROM read_csv_auto('{file_path.as_posix()}', header=True)")
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        LOG.info(f"Loaded {file_path.name} into {table_name} (Total rows: {count})")
        return count
    finally:
        if close_after:
            conn.close()


def run_query(query_name: str, conn: duckdb.DuckDBPyConnection = None):
    """Executes a named query from database/queries/."""
    sql_file = QUERIES_DIR / query_name
    if not sql_file.exists():
        sql_file = QUERIES_DIR / f"{query_name}.sql"
    if not sql_file.exists():
        raise FileNotFoundError(f"Query file {query_name} not found in {QUERIES_DIR}")

    with open(sql_file, "r", encoding="utf-8") as f:
        query_sql = f.read()

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        df = conn.execute(query_sql).df()
        return df
    finally:
        if close_after:
            conn.close()


def verify_database() -> dict:
    """Returns row counts for all tables in the database."""
    conn = get_connection()
    tables = [
        "prices", "universe", "corporate_actions", "signals",
        "trades", "strategy_returns", "factors", "nifty50", "trial_registry"
    ]
    summary = {}
    for t in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            summary[t] = cnt
        except Exception as e:
            summary[t] = f"Error: {e}"
    conn.close()
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DuckDB database loader and verifier")
    parser.add_argument("--init", action="store_true", help="Initialize schema")
    parser.add_argument("--verify", action="store_true", help="Verify tables and print row counts")
    parser.add_argument("--query", type=str, help="Run a specific query file name (e.g. q01_top_pairs_by_sharpe)")
    args = parser.parse_args()

    if args.init:
        init_schema()
    if args.verify:
        counts = verify_database()
        print("\n--- DuckDB Table Row Counts ---")
        for tbl, c in counts.items():
            print(f"  {tbl:<20}: {c}")
    if args.query:
        result_df = run_query(args.query)
        print(f"\n--- Results for {args.query} ---")
        print(result_df)
