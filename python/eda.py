"""
Exploratory data analysis, KPI calculation and charts (pandas
equivalent of sql/02_kpis.sql).

Input:  output/cleaned_transactions.csv
Output: output/kpi_summary.csv, output/eda_report.md, output/charts/*.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # write PNGs without needing a display
import matplotlib.dates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "output" / "cleaned_transactions.csv"
KPI_PATH = ROOT / "output" / "kpi_summary.csv"
REPORT_PATH = ROOT / "output" / "eda_report.md"
CHART_DIR = ROOT / "output" / "charts"

sns.set_theme(style="whitegrid")


def table(df) -> str:
    """Plain-text table inside a markdown code block (no extra dependencies)."""
    return "```\n" + df.to_string() + "\n```"


def save_chart(fig, name):
    fig.tight_layout()
    fig.savefig(CHART_DIR / name, dpi=120)
    plt.close(fig)


def make_charts(df, by_type, failed_rate, trend):
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(x=by_type.index, y=by_type["total_value"], ax=ax, color="#4C72B0")
    for i, pct in enumerate(by_type["pct_of_total"]):
        ax.text(i, by_type["total_value"].iloc[i], f"{pct:.1f}%", ha="center", va="bottom")
    ax.set(title="Successful value by transaction type", xlabel="", ylabel="Total value")
    save_chart(fig, "01_value_by_type.png")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(trend.index, trend["total_value"], marker="o")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    ax.set(title="Successful value per 5 minutes", xlabel="5-minute window ending at",
           ylabel="Total value")
    fig.autofmt_xdate()
    save_chart(fig, "02_value_trend_5min.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=df, x="amount", hue="status", bins=30, multiple="stack", ax=ax)
    ax.set(title="Transaction amount distribution", xlabel="Amount")
    save_chart(fig, "03_amount_distribution.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.boxplot(data=df, x="device_used", y="amount", hue="transaction_type", ax=ax)
    ax.set(title="Amount by device and transaction type", xlabel="", ylabel="Amount")
    save_chart(fig, "04_amount_by_device_type.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(x=failed_rate.index, y=failed_rate.values, ax=ax, color="#C44E52")
    ax.set(title="Failed-transaction rate by type", xlabel="", ylabel="Failed %")
    save_chart(fig, "05_failed_rate_by_type.png")

    fig, ax = plt.subplots(figsize=(6, 5))
    corr = df[["amount", "latency_ms", "bandwidth_mbps"]].assign(
        fraud_flag=df["fraud_flag"].astype(int)
    ).corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set(title="Correlation of numeric fields")
    save_chart(fig, "06_correlation_heatmap.png")


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

    # The whole dataset covers a single hour (10:01-11:00), so a daily
    # trend would be one row. Use 5-minute buckets instead, labelled by
    # their end time so 10:56-11:00 forms one full bucket.
    trend = (
        success.set_index("txn_timestamp")
        .resample("5min", closed="right", label="right")["amount"]
        .agg(txn_count="count", total_value="sum")
        .round(2)
    )

    fraud_count = int(df["fraud_flag"].sum())
    fraud_value = df.loc[df["fraud_flag"], "amount"].sum()
    fraud_by_type = (
        df.groupby("transaction_type")["fraud_flag"].mean().mul(100).round(2).rename("fraud_pct")
    )

    # Flat KPI summary CSV for the dashboard
    kpi_rows = [
        {"metric": "total_revenue_success", "value": round(total_value, 2)},
        {"metric": "transaction_volume_success", "value": txn_volume},
        {"metric": "avg_transaction_value", "value": round(avg_value, 2)},
        {"metric": "fraud_flagged_count", "value": fraud_count},
        {"metric": "fraud_flagged_value", "value": round(fraud_value, 2)},
    ]
    pd.DataFrame(kpi_rows).to_csv(KPI_PATH, index=False)

    make_charts(df, by_type, failed_rate, trend)

    start, end = df["txn_timestamp"].min(), df["txn_timestamp"].max()
    lines = [
        "# Exploratory Data Analysis\n",
        f"- Data covers **{start:%Y-%m-%d %H:%M}** to **{end:%H:%M}** ({len(df)} transactions)",
        f"- Total successful transaction value: **{total_value:,.2f}**",
        f"- Successful transaction volume: **{txn_volume}**",
        f"- Average transaction value: **{avg_value:,.2f}**",
        f"- Fraud-flagged transactions: **{fraud_count}** (value: {fraud_value:,.2f})\n",
        "## Contribution by transaction type\n",
        table(by_type),
        "\n![Value by type](charts/01_value_by_type.png)\n",
        "## Performance by device\n",
        table(by_device),
        "\n![Amount by device](charts/04_amount_by_device_type.png)\n",
        "## Failed-transaction rate by type (%)\n",
        table(failed_rate.to_frame()),
        "\n![Failed rate](charts/05_failed_rate_by_type.png)\n",
        "## Fraud-flag rate by type (%)\n",
        table(fraud_by_type.to_frame()),
        "\n## 5-minute trend (successful transactions)\n",
        table(trend),
        "\n![Trend](charts/02_value_trend_5min.png)\n",
        "## Amount distribution and correlations\n",
        "![Amount distribution](charts/03_amount_distribution.png)\n",
        "![Correlation heatmap](charts/06_correlation_heatmap.png)\n",
        "Correlations between amount, latency, bandwidth and `fraud_flag` are all close "
        "to zero, so `fraud_flag` cannot be predicted from these fields alone.",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Total value:   {total_value:,.2f}")
    print(f"Txn volume:    {txn_volume}")
    print(f"Avg value:     {avg_value:,.2f}")
    print(f"Fraud flagged: {fraud_count}")
    print(f"KPI summary written to:  {KPI_PATH}")
    print(f"EDA report written to:   {REPORT_PATH}")
    print(f"Charts written to:       {CHART_DIR}")


if __name__ == "__main__":
    sys.exit(main())
