# Analytical Workflow

## Pipeline
`python run_pipeline.py` runs these steps in order:

1. `python/clean_data.py`: loads the raw export, renames columns,
   deduplicates, fixes types, splits geolocation into
   latitude/longitude, and drops rows with missing required fields or
   negative amounts.
2. `python/eda.py`: computes KPIs (total value, transaction volume,
   average transaction value, contribution by type and device,
   failed-transaction rate, 5-minute trend), writes
   `output/eda_report.md`, and saves charts to `output/charts/`.
3. `python/anomaly_detection.py`: applies 7 rule checks to every
   transaction and adds up a score. Transactions with a score of 2 or
   more are written to `output/anomalies_review_list.csv`, ranked by
   score and then by how far amount, latency and bandwidth are from
   their averages.
4. `python/load_to_sqlite.py`: creates `output/transactions.db` from
   `sql/01_schema.sql`, loads the data, then runs
   `sql/02_kpis.sql` and `sql/03_anomaly_checks.sql` and saves each
   result to `output/sql_results/`. The SQL results match the pandas
   numbers, which cross-checks both.
5. `python/export_for_tableau.py`: joins the clean data and the
   anomaly scores into one wide file for the dashboard.

## Anomaly method and assumptions
- Rules use percentiles (top/bottom 5%) and z-scores, so they adapt
  to the data instead of using hard-coded amounts.
- Every rule counts as 1 point. The threshold of 2 points is an
  assumption: one unusual signal on its own is common (34% of
  transactions break at least one rule), two together are rarer
  (6.9%).
- The method is unsupervised. It does not use the dataset's own
  `fraud_flag` column; that column is only compared afterwards.
- The earlier version of this project used an Isolation Forest with
  hour of day as a feature. Since every transaction happens in hour 10
  except those at exactly 11:00, the model mostly flagged the 11:00
  rows. The rule-based approach avoids this and explains each flag.

## Limitations
- 1,000 transactions over a single hour is a small sample. Flagged
  transactions are a prioritized review list, not a fraud verdict.
- `fraud_flag` is True on about 48% of rows and shows almost no
  correlation with amount, latency or bandwidth (see the correlation
  heatmap). It looks randomly generated, so no method can match it
  well. Flagged transactions carry it 53.6% of the time vs. 48.1%
  overall.
- Amounts, latency and bandwidth are evenly spread (uniform), so there
  are no extreme outliers. Percentile rules are used instead of a
  "z-score above 3" rule for that reason.
- The dataset mixes retail-style fields (amount, type) with
  banking/network fields (PIN code, network slice, latency), and has
  no product or SKU data. Contribution KPIs are therefore reported by
  transaction type and device.
- Geolocation values are random pairs of a few city latitudes and
  longitudes, and every row ends in "W" even when the longitude is
  positive. The cleaned latitude/longitude keep the numbers as
  written, but location-based analysis is not meaningful.

## Recommendations
- Send flagged transactions in `output/anomalies_review_list.csv` to
  manual review, starting from priority rank 1, before acting on any
  of them.
- Watch the failed-transaction rate by type over time. A rising rate
  on one channel is often an earlier signal than fraud flags alone.
- Investigate the busiest minutes (10:25 and 10:55) for system load or
  scripted activity.
- If a true product/category dimension becomes available, add a
  `products` table to `sql/01_schema.sql` and re-run the contribution
  KPI against it.
- Once real labelled fraud cases exist, use them to tune the rule
  percentiles and the score threshold.
