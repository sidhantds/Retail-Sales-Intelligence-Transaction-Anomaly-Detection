# Retail Sales Intelligence & Transaction Anomaly Detection

End-to-end analytics and anomaly-detection pipeline on a 1,000-row
transaction dataset, using PostgreSQL, SQL, Python, and Tableau.

## What it does
- Normalized relational schema (`sql/01_schema.sql`) with primary
  and foreign keys across accounts, devices, network slices, and
  transactions.
- Data cleaning and validation (`python/clean_data.py`).
- KPI calculation and exploratory analysis — revenue, transaction
  volume, average transaction value, contribution by type and
  device — in both SQL (`sql/02_kpis.sql`) and Python
  (`python/eda.py`).
- Isolation Forest anomaly detection (`python/anomaly_detection.py`)
  on transaction-level features, producing a ranked, prioritized
  review list for fraud screening.
- A Tableau-ready extract and dashboard spec (`dashboard/`).
- Documented workflow, assumptions, limitations, and
  recommendations (`docs/workflow.md`).

## Quick start
```bash
git clone <this-repo>
cd retail-sales-intelligence
./setup.sh
```
This installs dependencies and runs the full pipeline: clean data
-> KPIs/EDA -> anomaly detection -> Tableau extract. Outputs land in
`output/` and `dashboard/`.

To also load the data into PostgreSQL:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
python3 python/load_to_postgres.py
```
Then run the KPI queries in `sql/02_kpis.sql` directly against the
database.

## Project layout
```
data/raw/               source CSV
sql/                     schema + KPI queries
python/                  cleaning, EDA, anomaly detection, loaders
dashboard/               Tableau extract + dashboard spec
output/                  generated KPI summaries, EDA report, review list
docs/                    workflow, assumptions, limitations
```

## Skills
SQL, PostgreSQL, Python, Pandas, NumPy, Scikit-learn, Isolation
Forest, Anomaly Detection, Data Cleaning, Data Validation,
Exploratory Data Analysis, Feature Engineering, KPI Reporting,
Business Intelligence, Tableau, Data Visualization, Relational
Database Design, Data-Driven Decision-Making

## Note on the source data
The original dataset mixes retail-style transaction fields (amount,
type, status) with banking/network fields (PIN code, network slice,
latency) rather than product/SKU-level data. KPIs and dashboards in
this rebuild are reported by transaction type and device rather than
by product category as a result — see `docs/workflow.md` for the
full list of assumptions and limitations.
