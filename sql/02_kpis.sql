-- ============================================================
-- KPI queries used for the dashboard and reporting layer.
-- Run after 01_schema.sql and loading data (python/load_to_postgres.py).
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
    COUNT(*)                                            AS txn_count,
    ROUND(SUM(amount), 2)                                AS total_value,
    ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 2) AS pct_of_total
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

-- 4. Daily trend
SELECT
    DATE(txn_timestamp)        AS txn_date,
    COUNT(*)                   AS txn_count,
    ROUND(SUM(amount), 2)      AS total_value
FROM transactions
WHERE status = 'Success'
GROUP BY DATE(txn_timestamp)
ORDER BY txn_date;

-- 5. Failed transaction rate by type
SELECT
    transaction_type,
    COUNT(*) FILTER (WHERE status = 'Failed')              AS failed_count,
    COUNT(*)                                                 AS total_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Failed') / COUNT(*), 2) AS failed_pct
FROM transactions
GROUP BY transaction_type
ORDER BY failed_pct DESC;

-- 6. Fraud-flagged transactions, highest value first
SELECT
    transaction_id,
    sender_account_id,
    receiver_account_id,
    amount,
    transaction_type,
    txn_timestamp,
    status
FROM transactions
WHERE fraud_flag = TRUE
ORDER BY amount DESC;

-- 7. Network slice latency vs. bandwidth summary
SELECT
    ns.slice_name,
    COUNT(*)                   AS txn_count,
    ROUND(AVG(t.latency_ms), 1)      AS avg_latency_ms,
    ROUND(AVG(t.bandwidth_mbps), 1)  AS avg_bandwidth_mbps
FROM transactions t
JOIN network_slices ns ON t.slice_id = ns.slice_id
GROUP BY ns.slice_name
ORDER BY ns.slice_name;
