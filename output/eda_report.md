# Exploratory Data Analysis

- Total successful transaction value: **384,742.91**
- Successful transaction volume: **487**
- Average transaction value: **790.03**
- Fraud-flagged transactions: **481** (value: 378,863.90)

## Contribution by transaction type

| transaction_type   |   txn_count |   total_value |   pct_of_total |
|:-------------------|------------:|--------------:|---------------:|
| Transfer           |         192 |        157221 |          40.86 |
| Deposit            |         150 |        119501 |          31.06 |
| Withdrawal         |         145 |        108021 |          28.08 |

## Performance by device

| device_used   |   txn_count |   total_value |   avg_value |
|:--------------|------------:|--------------:|------------:|
| Mobile        |         521 |        403209 |      773.91 |
| Desktop       |         479 |        367956 |      768.18 |

## Failed-transaction rate by type (%)

| transaction_type   |   failed_pct |
|:-------------------|-------------:|
| Withdrawal         |        53.23 |
| Deposit            |        52.53 |
| Transfer           |        48.66 |

## Daily trend (first 10 days)

| txn_timestamp       |   txn_count |   total_value |
|:--------------------|------------:|--------------:|
| 2025-01-17 00:00:00 |         487 |        384743 |