"""
Data cleaning and validation for the raw transaction export.

Input:  data/raw/transaction_data.csv
Output: output/cleaned_transactions.csv
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "transaction_data.csv"
OUT_PATH = ROOT / "output" / "cleaned_transactions.csv"


def parse_geolocation(value: str):
    """Split 'lat N/S, lon E/W' into signed decimal degrees."""
    if not isinstance(value, str):
        return (None, None)
    m = re.match(
        r"\s*([\d.]+)\s*([NS])\s*,\s*(-?[\d.]+)\s*([EW])\s*", value
    )
    if not m:
        return (None, None)
    lat, lat_dir, lon, lon_dir = m.groups()
    lat = float(lat) * (1 if lat_dir == "N" else -1)
    lon = float(lon) * (1 if lon_dir == "E" else -1)
    return (lat, lon)


def main():
    df = pd.read_csv(RAW_PATH)
    n_raw = len(df)

    # Standardize column names
    df.columns = [
        "transaction_id",
        "sender_account_id",
        "receiver_account_id",
        "amount",
        "transaction_type",
        "txn_timestamp",
        "status",
        "fraud_flag",
        "geolocation",
        "device_used",
        "network_slice_id",
        "latency_ms",
        "bandwidth_mbps",
        "pin_code",
    ]

    # Drop exact duplicate rows and duplicate transaction ids
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="transaction_id", keep="first")

    # Type conversions and validation
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["txn_timestamp"] = pd.to_datetime(df["txn_timestamp"], errors="coerce")
    df["fraud_flag"] = df["fraud_flag"].astype(str).str.strip().str.lower().map(
        {"true": True, "false": False}
    )
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    df["bandwidth_mbps"] = pd.to_numeric(df["bandwidth_mbps"], errors="coerce")

    # Split geolocation into latitude / longitude
    lat_lon = df["geolocation"].apply(parse_geolocation)
    df["latitude"] = lat_lon.apply(lambda t: t[0])
    df["longitude"] = lat_lon.apply(lambda t: t[1])
    df = df.drop(columns=["geolocation"])

    # Drop rows missing required fields
    required = ["transaction_id", "amount", "txn_timestamp", "transaction_type", "status"]
    before = len(df)
    df = df.dropna(subset=required)
    dropped_missing = before - len(df)

    # Drop invalid amounts (negative)
    before = len(df)
    df = df[df["amount"] >= 0]
    dropped_negative = before - len(df)

    # Normalize text fields
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    df["status"] = df["status"].str.strip().str.title()
    df["device_used"] = df["device_used"].str.strip()
    df["network_slice_id"] = df["network_slice_id"].str.strip()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Raw rows:            {n_raw}")
    print(f"Dropped (missing req): {dropped_missing}")
    print(f"Dropped (negative amount): {dropped_negative}")
    print(f"Clean rows:           {len(df)}")
    print(f"Written to:           {OUT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
