-- ============================================================
-- Schema: transaction intelligence database
-- Normalized into dimension tables (accounts, devices, network
-- slices) and one fact table (transactions) with primary and
-- foreign keys.
-- ============================================================

DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS network_slices CASCADE;

CREATE TABLE accounts (
    account_id      VARCHAR(20) PRIMARY KEY
);

CREATE TABLE devices (
    device_id       SERIAL PRIMARY KEY,
    device_name     VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE network_slices (
    slice_id        SERIAL PRIMARY KEY,
    slice_name      VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE transactions (
    transaction_id      VARCHAR(20) PRIMARY KEY,
    sender_account_id    VARCHAR(20) REFERENCES accounts(account_id),
    receiver_account_id  VARCHAR(20) REFERENCES accounts(account_id),
    amount               NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    transaction_type      VARCHAR(20) NOT NULL,  -- Deposit / Withdrawal / Transfer
    txn_timestamp          TIMESTAMP NOT NULL,
    status                VARCHAR(20) NOT NULL,  -- Success / Failed
    fraud_flag            BOOLEAN NOT NULL DEFAULT FALSE,
    latitude              NUMERIC(9,6),
    longitude             NUMERIC(9,6),
    device_id             INTEGER REFERENCES devices(device_id),
    slice_id              INTEGER REFERENCES network_slices(slice_id),
    latency_ms             INTEGER,
    bandwidth_mbps          INTEGER,
    pin_code               VARCHAR(10)
);

CREATE INDEX idx_txn_timestamp ON transactions(txn_timestamp);
CREATE INDEX idx_txn_type ON transactions(transaction_type);
CREATE INDEX idx_txn_fraud ON transactions(fraud_flag);
