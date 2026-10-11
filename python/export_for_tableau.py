"""
Builds a flat, denormalized extract for Tableau (one row per
transaction with all dimension fields already joined in, since
Tableau works best off a single wide table).

Input:  output/cleaned_transactions.csv, output/anomalies_review_list.csv
Output: dashboard/tableau_extract.csv
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH = ROOT / "output" / "cleaned_transactions.csv"
ANOMALY_PATH = ROOT / "output" / "anomalies_review_list.csv"
OUT_PATH = ROOT / "dashboard" / "tableau_extract.csv"


def main():
    df = pd.read_csv(CLEAN_PATH, parse_dates=["txn_timestamp"])
    anomalies = pd.read_csv(ANOMALY_PATH)

    df["is_anomaly"] = df["transaction_id"].isin(anomalies["transaction_id"])
    df["txn_date"] = df["txn_timestamp"].dt.date
    df["txn_hour"] = df["txn_timestamp"].dt.hour
    df["day_of_week"] = df["txn_timestamp"].dt.day_name()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Tableau extract written to: {OUT_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    sys.exit(main())
