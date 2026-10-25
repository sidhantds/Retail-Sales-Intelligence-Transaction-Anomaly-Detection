-- ============================================================
-- KPI queries used for the dashboard and reporting layer.
-- Run after python/load_to_sqlite.py (which also runs this file
-- and saves each result to output/sql_results/).
-- ============================================================

-- 1. Total transaction value and volume
SELECT
    COUNT(*)                   AS transaction_volume,
    ROUND(SUM(amount), 2)      AS total_value,
    ROUND(AVG(amount), 2)      AS avg_transaction_value
FROM transactions
WHERE status = 'Success';

-- 2. Contribution by transaction type
SELECT
    transaction_type,
    COUNT(*)                                                  AS txn_count,
    ROUND(SUM(amount), 2)                                     AS total_value,
    ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 2)  AS pct_of_total
FROM transactions
WHERE status = 'Success'
GROUP BY transaction_type
ORDER BY total_value DESC;

-- 3. Performance by device used
SELECT
    d.device_name,
    COUNT(*)                   AS txn_count,
    ROUND(SUM(t.amount), 2)    AS total_value,
    ROUND(AVG(t.amount), 2)    AS avg_value
FROM transactions t
JOIN devices d ON t.device_id = d.device_id
GROUP BY d.device_name
ORDER BY total_value DESC;

-- 4. 5-minute trend (the data covers a single hour, so a daily
--    trend would be one row). Each window is labelled by its end
--    time: 10:01-10:05 -> "10:05", ..., 10:56-11:00 -> "11:00".
SELECT
    STRFTIME('%H:%M', txn_timestamp,
        '+' || ((5 - CAST(STRFTIME('%M', txn_timestamp) AS INTEGER) % 5) % 5) || ' minutes')
                               AS time_bucket,
    COUNT(*)                   AS txn_count,
    ROUND(SUM(amount), 2)      AS total_value
FROM transactions
WHERE status = 'Success'
GROUP BY time_bucket
ORDER BY time_bucket;

-- 5. Failed transaction rate by type
SELECT
    transaction_type,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END)                       AS failed_count,
    COUNT(*)                                                                 AS total_count,
    ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failed_pct
FROM transactions
GROUP BY transaction_type
ORDER BY failed_pct DESC;

-- 6. Fraud-flagged transactions, highest value first (top 20)
SELECT
    transaction_id,
    sender_account_id,
    receiver_account_id,
    amount,
    transaction_type,
    txn_timestamp,
    status
FROM transactions
WHERE fraud_flag = 1
ORDER BY amount DESC
LIMIT 20;

-- 7. Network slice latency vs. bandwidth summary
SELECT
    ns.slice_name,
    COUNT(*)                         AS txn_count,
    ROUND(AVG(t.latency_ms), 1)      AS avg_latency_ms,
    ROUND(AVG(t.bandwidth_mbps), 1)  AS avg_bandwidth_mbps
FROM transactions t
JOIN network_slices ns ON t.slice_id = ns.slice_id
GROUP BY ns.slice_name
ORDER BY ns.slice_name;
