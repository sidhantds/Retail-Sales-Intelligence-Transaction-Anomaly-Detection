"""
Loads the cleaned data into a SQLite database using the schema in
sql/01_schema.sql, then runs every query in sql/02_kpis.sql and
sql/03_anomaly_checks.sql and saves each result as a CSV.

SQLite comes with Python, so no database server or extra package
is needed. The database file can be opened in DB Browser for SQLite,
DBeaver, or the VS Code SQLite extension.

Input:  output/cleaned_transactions.csv
Output: output/transactions.db, output/sql_results/*.csv
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"
DB_PATH = ROOT / "output" / "transactions.db"
RESULTS_DIR = ROOT / "output" / "sql_results"
QUERY_FILES = ["02_kpis.sql", "03_anomaly_checks.sql"]


def split_queries(sql_text: str):
    """Split a .sql file into (title, query) pairs on ';'."""
    for chunk in sql_text.split(";"):
        lines = chunk.strip().splitlines()
        comments = [l.strip("- ").strip() for l in lines if l.strip().startswith("--")]
        body = "\n".join(l for l in lines if not l.strip().startswith("--")).strip()
        if body:
            # Last numbered comment above the query is its title, e.g. "1. Busiest minutes"
            numbered = [c for c in comments if c[:1].isdigit()]
            yield (numbered[-1] if numbered else "query"), body


def main():
    df = pd.read_csv(IN_PATH)
    df["fraud_flag"] = df["fraud_flag"].astype(int)

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript((ROOT / "sql" / "01_schema.sql").read_text())

        accounts = pd.DataFrame(
            pd.concat([df["sender_account_id"], df["receiver_account_id"]]).unique(),
            columns=["account_id"],
        )
        devices = pd.DataFrame(sorted(df["device_used"].dropna().unique()), columns=["device_name"])
        slices = pd.DataFrame(sorted(df["network_slice_id"].dropna().unique()), columns=["slice_name"])

        accounts.to_sql("accounts", conn, if_exists="append", index=False)
        devices.to_sql("devices", conn, if_exists="append", index=False)
        slices.to_sql("network_slices", conn, if_exists="append", index=False)

        device_map = pd.read_sql("SELECT device_id, device_name FROM devices", conn)
        slice_map = pd.read_sql("SELECT slice_id, slice_name FROM network_slices", conn)

        txns = (
            df.merge(device_map, left_on="device_used", right_on="device_name")
            .merge(slice_map, left_on="network_slice_id", right_on="slice_name")
        )[[
            "transaction_id", "sender_account_id", "receiver_account_id", "amount",
            "transaction_type", "txn_timestamp", "status", "fraud_flag",
            "latitude", "longitude", "device_id", "slice_id",
            "latency_ms", "bandwidth_mbps", "pin_code",
        ]]
        txns.to_sql("transactions", conn, if_exists="append", index=False)
        print(f"Loaded {len(txns)} transactions into {DB_PATH}")

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        for file_name in QUERY_FILES:
            sql_text = (ROOT / "sql" / file_name).read_text()
            for i, (title, query) in enumerate(split_queries(sql_text), start=1):
                result = pd.read_sql(query, conn)
                out = RESULTS_DIR / f"{Path(file_name).stem}_{i}.csv"
                result.to_csv(out, index=False)
                print(f"  {file_name} #{i} {title[:45]:<45} -> {len(result)} rows")

    print(f"SQL results written to: {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
