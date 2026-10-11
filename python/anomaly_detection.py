"""
Isolation Forest anomaly detection on transaction-level features.

Input:  output/cleaned_transactions.csv
Output: output/anomalies_review_list.csv, output/anomaly_summary.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"
OUT_PATH = ROOT / "output" / "anomalies_review_list.csv"
SUMMARY_PATH = ROOT / "output" / "anomaly_summary.md"

CONTAMINATION = 0.05   # assumed share of transactions worth flagging
RANDOM_STATE = 42


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df[["amount", "latency_ms", "bandwidth_mbps"]].copy()

    # Hour of day captures off-hours activity, a common fraud signal
    numeric["hour_of_day"] = pd.to_datetime(df["txn_timestamp"]).dt.hour

    categorical = df[["transaction_type", "status", "device_used", "network_slice_id"]]
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    cat_encoded = enc.fit_transform(categorical)
    cat_df = pd.DataFrame(
        cat_encoded, columns=enc.get_feature_names_out(categorical.columns), index=df.index
    )

    features = pd.concat([numeric, cat_df], axis=1)
    return features.fillna(0)


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["txn_timestamp"])
    features = build_features(df)

    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
    )
    model.fit(features)

    df["anomaly_score"] = model.decision_function(features)   # higher = more normal
    df["is_anomaly"] = model.predict(features) == -1          # True = flagged

    review = df[df["is_anomaly"]].copy()
    review["priority_rank"] = review["anomaly_score"].rank(method="first").astype(int)
    review = review.sort_values("anomaly_score")  # most anomalous first

    cols = [
        "transaction_id", "sender_account_id", "receiver_account_id", "amount",
        "transaction_type", "txn_timestamp", "status", "fraud_flag",
        "device_used", "network_slice_id", "latency_ms", "bandwidth_mbps",
        "anomaly_score",
    ]
    review[cols].to_csv(OUT_PATH, index=False)

    # How well the model's flags line up with the dataset's own fraud_flag label
    overlap = int((review["fraud_flag"]).sum())
    total_flagged = len(review)
    total_fraud_labeled = int(df["fraud_flag"].sum())

    lines = [
        "# Anomaly Detection Summary\n",
        f"- Model: Isolation Forest (contamination={CONTAMINATION}, n_estimators=200)",
        f"- Transactions scored: {len(df)}",
        f"- Transactions flagged as anomalous: {total_flagged}",
        f"- Flagged transactions that also carry fraud_flag=True: {overlap} "
        f"({100 * overlap / total_flagged:.1f}% of flagged, if any)" if total_flagged else "",
        f"- Total fraud_flag=True in dataset: {total_fraud_labeled}",
        "",
        "Flagged transactions are written to `output/anomalies_review_list.csv`, "
        "ranked from most to least anomalous, for manual fraud-screening review.",
    ]
    SUMMARY_PATH.write_text("\n".join(l for l in lines if l is not None))

    print(f"Scored:  {len(df)}")
    print(f"Flagged: {total_flagged}")
    print(f"Review list written to: {OUT_PATH}")
    print(f"Summary written to:     {SUMMARY_PATH}")


if __name__ == "__main__":
    sys.exit(main())
