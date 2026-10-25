"""
Rule-based statistical anomaly detection (pandas + NumPy only).

Each transaction is checked against a set of simple, explainable
rules built from percentiles and z-scores. Every rule it breaks adds
one point to its anomaly score, and the rules it broke are listed in
`anomaly_reasons`, so a reviewer can see *why* it was flagged.

Input:  output/cleaned_transactions.csv
Output: output/anomalies_review_list.csv, output/anomaly_summary.md,
        output/charts/07_anomalies_scatter.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"
OUT_PATH = ROOT / "output" / "anomalies_review_list.csv"
SUMMARY_PATH = ROOT / "output" / "anomaly_summary.md"
CHART_PATH = ROOT / "output" / "charts" / "07_anomalies_scatter.png"

FLAG_THRESHOLD = 2   # a transaction must break at least this many rules
Z_LIMIT = 2.0        # z-score above which a minute counts as a burst

sns.set_theme(style="whitegrid")


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Return one True/False column per rule."""
    rules = pd.DataFrame(index=df.index)

    # 1. Very large amount (top 5%)
    rules["high_amount"] = df["amount"] >= df["amount"].quantile(0.95)

    # 2. Large amount that failed (top 10% amount + Failed status)
    rules["failed_high_value"] = (df["status"] == "Failed") & (
        df["amount"] >= df["amount"].quantile(0.90)
    )

    # 3. Network looked unusual: very high latency or very low bandwidth
    rules["high_latency"] = df["latency_ms"] >= df["latency_ms"].quantile(0.95)
    rules["low_bandwidth"] = df["bandwidth_mbps"] <= df["bandwidth_mbps"].quantile(0.05)

    # 4. Happened in a minute with an unusually high number of transactions
    minute = df["txn_timestamp"].dt.floor("min")
    minute_counts = minute.value_counts()
    burst_minutes = minute_counts[zscore(minute_counts) > Z_LIMIT].index
    rules["burst_minute"] = minute.isin(burst_minutes)

    # 5. Account shows up in more than one transaction (sender or receiver)
    all_accounts = pd.concat([df["sender_account_id"], df["receiver_account_id"]])
    repeat_accounts = all_accounts.value_counts()
    repeat_accounts = repeat_accounts[repeat_accounts > 1].index
    rules["repeat_account"] = df["sender_account_id"].isin(repeat_accounts) | df[
        "receiver_account_id"
    ].isin(repeat_accounts)

    # 6. Same PIN code used by more than one sender account
    senders_per_pin = df.groupby("pin_code")["sender_account_id"].transform("nunique")
    rules["shared_pin"] = senders_per_pin > 1

    return rules


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["txn_timestamp"])
    rules = apply_rules(df)

    df["anomaly_score"] = rules.sum(axis=1)
    df["anomaly_reasons"] = rules.apply(lambda row: ", ".join(row.index[row]), axis=1)
    df["is_anomaly"] = df["anomaly_score"] >= FLAG_THRESHOLD

    # Tie-breaker inside the same score: how far amount/latency/bandwidth
    # are from normal, combined into one number
    df["deviation"] = np.sqrt(
        zscore(df["amount"]) ** 2
        + zscore(df["latency_ms"]) ** 2
        + zscore(df["bandwidth_mbps"]) ** 2
    ).round(3)

    review = df[df["is_anomaly"]].sort_values(
        ["anomaly_score", "deviation", "amount"], ascending=False
    ).copy()
    review["priority_rank"] = np.arange(1, len(review) + 1)

    cols = [
        "priority_rank", "transaction_id", "sender_account_id", "receiver_account_id",
        "amount", "transaction_type", "txn_timestamp", "status", "fraud_flag",
        "device_used", "network_slice_id", "latency_ms", "bandwidth_mbps",
        "anomaly_score", "anomaly_reasons", "deviation",
    ]
    review[cols].to_csv(OUT_PATH, index=False)

    # Save every transaction's score too, for the Tableau extract
    df[["transaction_id", "anomaly_score", "anomaly_reasons", "is_anomaly"]].to_csv(
        ROOT / "output" / "anomaly_scores.csv", index=False
    )

    CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=df, x="amount", y="latency_ms", hue="is_anomaly",
        palette={False: "#B0B0B0", True: "#C44E52"}, alpha=0.7, ax=ax,
    )
    ax.legend(title="Flagged", loc="upper left", bbox_to_anchor=(1, 1))
    ax.set(title="Flagged transactions (red) by amount and latency",
           xlabel="Amount", ylabel="Latency (ms)")
    fig.tight_layout()
    fig.savefig(CHART_PATH, dpi=120)
    plt.close(fig)

    # Summary
    total_flagged = len(review)
    overlap = int(review["fraud_flag"].sum())
    total_fraud_labeled = int(df["fraud_flag"].sum())
    base_rate = 100 * total_fraud_labeled / len(df)
    rule_counts = rules.sum().sort_values(ascending=False)
    score_counts = df["anomaly_score"].value_counts().sort_index()

    lines = [
        "# Anomaly Detection Summary\n",
        f"- Method: rule-based scoring (percentiles + z-scores), flag if score >= {FLAG_THRESHOLD}",
        f"- Transactions scored: {len(df)}",
        f"- Transactions flagged: {total_flagged} ({100 * total_flagged / len(df):.1f}%)",
    ]
    if total_flagged:
        lines.append(
            f"- Flagged transactions that also carry fraud_flag=True: {overlap} "
            f"({100 * overlap / total_flagged:.1f}% of flagged, vs. {base_rate:.1f}% overall)"
        )
    lines += [
        f"- Total fraud_flag=True in dataset: {total_fraud_labeled}\n",
        "## How often each rule fired\n",
        "```\n" + rule_counts.to_string() + "\n```\n",
        "## Transactions by anomaly score\n",
        "```\n" + score_counts.to_string() + "\n```\n",
        "![Flagged transactions](charts/07_anomalies_scatter.png)\n",
        "Flagged transactions are written to `output/anomalies_review_list.csv`, "
        "highest priority first, with the reasons for each flag.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Scored:  {len(df)}")
    print(f"Flagged: {total_flagged}")
    print(f"Review list written to: {OUT_PATH}")
    print(f"Summary written to:     {SUMMARY_PATH}")


if __name__ == "__main__":
    sys.exit(main())
