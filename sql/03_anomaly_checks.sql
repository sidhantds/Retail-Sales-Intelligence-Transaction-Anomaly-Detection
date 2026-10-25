-- ============================================================
-- SQL version of the main anomaly rules in
-- python/anomaly_detection.py, using CTEs and window functions.
-- NTILE(20) splits rows into 20 equal groups, so group 20 is the
-- top 5% and group 1 is the bottom 5%.
-- ============================================================

-- 1. Busiest minutes (the "burst_minute" rule)
SELECT
    STRFTIME('%H:%M', txn_timestamp)  AS txn_minute,
    COUNT(*)                          AS txn_count
FROM transactions
GROUP BY txn_minute
ORDER BY txn_count DESC
LIMIT 5;

-- 2. Accounts that appear in more than one transaction
WITH all_accounts AS (
    SELECT sender_account_id AS account_id FROM transactions
    UNION ALL
    SELECT receiver_account_id FROM transactions
)
SELECT account_id, COUNT(*) AS appearances
FROM all_accounts
GROUP BY account_id
HAVING COUNT(*) > 1
ORDER BY appearances DESC, account_id;

-- 3. Rule score per transaction, highest first
WITH ranked AS (
    SELECT
        t.*,
        NTILE(20) OVER (ORDER BY amount)          AS amount_tile,
        NTILE(20) OVER (ORDER BY latency_ms)      AS latency_tile,
        NTILE(20) OVER (ORDER BY bandwidth_mbps)  AS bandwidth_tile
    FROM transactions t
),
scored AS (
    SELECT
        transaction_id,
        amount,
        transaction_type,
        status,
        latency_ms,
        bandwidth_mbps,
        fraud_flag,
        (amount_tile = 20)
          + (status = 'Failed' AND amount_tile >= 19)
          + (latency_tile = 20)
          + (bandwidth_tile = 1)          AS rule_score
    FROM ranked
)
SELECT *
FROM scored
WHERE rule_score >= 2
ORDER BY rule_score DESC, amount DESC;
