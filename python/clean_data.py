"""
Data cleaning and validation for the raw transaction export.

Input:  data/raw/transaction_data.csv
Output: output/cleaned_transactions.csv
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "transaction_data.csv"
OUT_PATH = ROOT / "output" / "cleaned_transactions.csv"

COLUMN_NAMES = {
    "Transaction ID": "transaction_id",
    "Sender Account ID": "sender_account_id",
    "Receiver Account ID": "receiver_account_id",
    "Transaction Amount": "amount",
    "Transaction Type": "transaction_type",
    "Timestamp": "txn_timestamp",
    "Transaction Status": "status",
    "Fraud Flag": "fraud_flag",
    "Geolocation (Latitude/Longitude)": "geolocation",
    "Device Used": "device_used",
    "Network Slice ID": "network_slice_id",
    "Latency (ms)": "latency_ms",
    "Slice Bandwidth (Mbps)": "bandwidth_mbps",
    "PIN Code": "pin_code",
}


def main():
    df = pd.read_csv(RAW_PATH)
    n_raw = len(df)

    # Rename by name (not position) so a reordered export still works
    df = df.rename(columns=COLUMN_NAMES)

    # Drop exact duplicate rows and duplicate transaction ids
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="transaction_id", keep="first")
    dropped_duplicates = n_raw - len(df)

    # Type conversions and validation
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["txn_timestamp"] = pd.to_datetime(df["txn_timestamp"], errors="coerce")
    df["fraud_flag"] = df["fraud_flag"].astype(str).str.strip().str.lower().map(
        {"true": True, "false": False}
    )
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    df["bandwidth_mbps"] = pd.to_numeric(df["bandwidth_mbps"], errors="coerce")

    # Split geolocation ("34.0522 N, -74.006 W") into latitude / longitude.
    # Every row in the source ends in "W", even ones with positive
    # longitudes, so the letter is unreliable. Keep the signed number as
    # written and drop the letters.
    geo = df["geolocation"].str.replace(r"[NSEW]", "", regex=True).str.split(",", expand=True)
    df["latitude"] = pd.to_numeric(geo[0], errors="coerce")
    df["longitude"] = pd.to_numeric(geo[1], errors="coerce")
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

    print(f"Raw rows:                  {n_raw}")
    print(f"Dropped (duplicates):      {dropped_duplicates}")
    print(f"Dropped (missing req):     {dropped_missing}")
    print(f"Dropped (negative amount): {dropped_negative}")
    print(f"Clean rows:                {len(df)}")
    print(f"Written to:                {OUT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
