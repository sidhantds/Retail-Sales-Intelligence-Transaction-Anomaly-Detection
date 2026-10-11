# Analytical Workflow

## Pipeline
1. `python/clean_data.py` — loads the raw export, deduplicates,
   fixes types, splits geolocation into latitude/longitude, drops
   rows with missing required fields or negative amounts.
2. `python/eda.py` — computes KPIs (total value, transaction
   volume, average transaction value, contribution by type and
   device, failed-transaction rate, daily trend) and writes a
   summary report.
3. `python/anomaly_detection.py` — trains an Isolation Forest on
   transaction-level features (amount, latency, bandwidth, hour of
   day, transaction type, status, device, network slice) and writes
   a ranked review list of flagged transactions.
4. `python/export_for_tableau.py` — joins the clean data and the
   anomaly flags into one wide file for the dashboard.
5. `python/load_to_postgres.py` (optional) — loads the same data
   into PostgreSQL using `sql/01_schema.sql`, if `DATABASE_URL` is
   set.
6. `sql/02_kpis.sql` — the same KPIs as `eda.py`, written as SQL for
   use directly against the Postgres database.

## Model assumptions
- Contamination rate of 5% (roughly 1 in 20 transactions) is an
  assumption, not derived from the data; it sets how many
  transactions the Isolation Forest flags.
- Features are a mix of numeric (amount, latency, bandwidth, hour
  of day) and one-hot encoded categorical fields (transaction type,
  status, device, network slice). No scaling is applied, since
  Isolation Forest splits on raw feature values and is not
  distance-based.
- The model is unsupervised: it does not use the dataset's own
  `fraud_flag` column during training. That column is only used
  afterward, to check how much the model's flags overlap with it.

## Limitations
- 1,000 transactions is a small sample for a tree-based anomaly
  model; flagged transactions should be treated as a prioritized
  review list, not a fraud verdict.
- The dataset mixes retail-style fields (transaction amount, type)
  with banking/network fields (PIN code, network slice, latency),
  so some KPIs (for example "category contribution") are reported
  by transaction type and device rather than by product category,
  since no product or SKU-level data is present in the source file.
- Geolocation values are a small set of repeated city coordinates
  rather than per-transaction GPS points, so the anomaly map and any
  location-based analysis reflect clusters of a few fixed points,
  not genuine transaction-level geography.
- No held-out labeled fraud set exists to measure precision/recall;
  the overlap with `fraud_flag` in `anomaly_summary.md` is
  informational only.

## Recommendations
- Route flagged transactions in `output/anomalies_review_list.csv`
  to manual review before taking action on any of them.
- Track the failed-transaction rate by type over time; a rising
  rate on one channel (for example Mobile) is often an earlier
  signal than fraud flags alone.
- If a true product/category dimension becomes available, extend
  `sql/01_schema.sql` with a `products` table and re-run the
  category-contribution KPI against it.
- Retrain the Isolation Forest periodically as new transactions
  arrive, and re-check the contamination assumption against the
  actual flagged rate over time.
