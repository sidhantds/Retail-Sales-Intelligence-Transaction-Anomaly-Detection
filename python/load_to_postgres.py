"""
Optional loader: pushes the cleaned data into PostgreSQL using the
schema in sql/01_schema.sql. Skipped automatically if DATABASE_URL
is not set or psycopg2 is not installed, so the rest of the
pipeline (cleaning, EDA, anomaly detection) never depends on this.

Usage:
    export DATABASE_URL=postgresql://user:pass@host:5432/dbname
    python python/load_to_postgres.py
"""
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"


def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set, skipping Postgres load. "
              "(SQL schema and KPI queries are still in sql/ for later use.)")
        return 0

    try:
        from sqlalchemy import create_engine
    except ImportError:
        print("sqlalchemy/psycopg2 not installed, skipping Postgres load. "
              "Install with: pip install sqlalchemy psycopg2-binary")
        return 0

    schema_sql = (ROOT / "sql" / "01_schema.sql").read_text()
    engine = create_engine(db_url)

    with engine.begin() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.exec_driver_sql(statement)

    df = pd.read_csv(IN_PATH, parse_dates=["txn_timestamp"])

    accounts = pd.DataFrame(
        pd.concat([df["sender_account_id"], df["receiver_account_id"]]).unique(),
        columns=["account_id"],
    )
    devices = pd.DataFrame(df["device_used"].dropna().unique(), columns=["device_name"])
    slices = pd.DataFrame(df["network_slice_id"].dropna().unique(), columns=["slice_name"])

    with engine.begin() as conn:
        accounts.to_sql("accounts", conn, if_exists="append", index=False)
        devices.to_sql("devices", conn, if_exists="append", index=False)
        slices.to_sql("network_slices", conn, if_exists="append", index=False)

    device_map = pd.read_sql("SELECT device_id, device_name FROM devices", engine)
    slice_map = pd.read_sql("SELECT slice_id, slice_name FROM network_slices", engine)

    txns = df.rename(columns={
        "sender_account_id": "sender_account_id",
        "receiver_account_id": "receiver_account_id",
    }).merge(device_map, left_on="device_used", right_on="device_name") \
      .merge(slice_map, left_on="network_slice_id", right_on="slice_name")

    txns = txns[[
        "transaction_id", "sender_account_id", "receiver_account_id", "amount",
        "transaction_type", "txn_timestamp", "status", "fraud_flag",
        "latitude", "longitude", "device_id", "slice_id",
        "latency_ms", "bandwidth_mbps", "pin_code",
    ]]

    with engine.begin() as conn:
        txns.to_sql("transactions", conn, if_exists="append", index=False)

    print(f"Loaded {len(txns)} transactions into {db_url.split('@')[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
