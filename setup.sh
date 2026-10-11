#!/usr/bin/env bash
# Rebuilds the full pipeline: clean -> EDA/KPIs -> anomaly detection
# -> Tableau extract. Postgres load is skipped unless DATABASE_URL
# is set, since it needs a live database.
set -e

cd "$(dirname "$0")"

echo "[1/5] Installing dependencies..."
pip install -q -r requirements.txt

echo "[2/5] Cleaning data..."
python3 python/clean_data.py

echo "[3/5] Running EDA and KPIs..."
python3 python/eda.py

echo "[4/5] Running anomaly detection..."
python3 python/anomaly_detection.py

echo "[5/5] Building Tableau extract..."
python3 python/export_for_tableau.py

echo
echo "Done. Optional: set DATABASE_URL and run"
echo "  python3 python/load_to_postgres.py"
echo "to load the data into PostgreSQL and use sql/02_kpis.sql."
