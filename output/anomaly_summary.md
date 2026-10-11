# Anomaly Detection Summary

- Model: Isolation Forest (contamination=0.05, n_estimators=200)
- Transactions scored: 1000
- Transactions flagged as anomalous: 50
- Flagged transactions that also carry fraud_flag=True: 28 (56.0% of flagged, if any)
- Total fraud_flag=True in dataset: 481

Flagged transactions are written to `output/anomalies_review_list.csv`, ranked from most to least anomalous, for manual fraud-screening review.