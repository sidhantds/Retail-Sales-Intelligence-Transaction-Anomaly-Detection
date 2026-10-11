"""
Exploratory data analysis and KPI calculation (pandas equivalent
of sql/02_kpis.sql, so the project works without a live Postgres
instance).

Input:  output/cleaned_transactions.csv
Output: output/kpi_summary.csv, output/eda_report.md
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"
KPI_PATH = ROOT / "output" / "kpi_summary.csv"
REPORT_PATH = ROOT / "output" / "eda_report.md"


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["txn_timestamp"])
    success = df[df["status"] == "Success"]

    total_value = success["amount"].sum()
    txn_volume = len(success)
    avg_value = success["amount"].mean()

    by_type = (
        success.groupby("transaction_type")["amount"]
        .agg(txn_count="count", total_value="sum")
        .assign(pct_of_total=lambda d: 100 * d["total_value"] / d["total_value"].sum())
        .sort_values("total_value", ascending=False)
        .round(2)
    )

    by_device = (
        df.groupby("device_used")["amount"]
        .agg(txn_count="count", total_value="sum", avg_value="mean")
        .sort_values("total_value", ascending=False)
        .round(2)
    )

    failed_rate = (
        df.groupby("transaction_type")["status"]
        .apply(lambda s: round(100 * (s == "Failed").mean(), 2))
        .rename("failed_pct")
        .sort_values(ascending=False)
    )

    daily_trend = (
        success.set_index("txn_timestamp")
        .resample("D")["amount"]
        .agg(txn_count="count", total_value="sum")
        .round(2)
    )

    fraud_count = int(df["fraud_flag"].sum())
    fraud_value = df.loc[df["fraud_flag"], "amount"].sum()

    # Write a flat KPI summary CSV for the dashboard
    kpi_rows = [
        {"metric": "total_revenue_success", "value": round(total_value, 2)},
        {"metric": "transaction_volume_success", "value": txn_volume},
        {"metric": "avg_transaction_value", "value": round(avg_value, 2)},
        {"metric": "fraud_flagged_count", "value": fraud_count},
        {"metric": "fraud_flagged_value", "value": round(fraud_value, 2)},
    ]
    pd.DataFrame(kpi_rows).to_csv(KPI_PATH, index=False)

    # Markdown EDA report
    lines = []
    lines.append("# Exploratory Data Analysis\n")
    lines.append(f"- Total successful transaction value: **{total_value:,.2f}**")
    lines.append(f"- Successful transaction volume: **{txn_volume}**")
    lines.append(f"- Average transaction value: **{avg_value:,.2f}**")
    lines.append(f"- Fraud-flagged transactions: **{fraud_count}** (value: {fraud_value:,.2f})\n")

    lines.append("## Contribution by transaction type\n")
    lines.append(by_type.to_markdown())
    lines.append("\n## Performance by device\n")
    lines.append(by_device.to_markdown())
    lines.append("\n## Failed-transaction rate by type (%)\n")
    lines.append(failed_rate.to_markdown())
    lines.append("\n## Daily trend (first 10 days)\n")
    lines.append(daily_trend.head(10).to_markdown())

    REPORT_PATH.write_text("\n".join(lines))

    print(f"Total value:   {total_value:,.2f}")
    print(f"Txn volume:    {txn_volume}")
    print(f"Avg value:     {avg_value:,.2f}")
    print(f"Fraud flagged: {fraud_count}")
    print(f"KPI summary written to:  {KPI_PATH}")
    print(f"EDA report written to:   {REPORT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
