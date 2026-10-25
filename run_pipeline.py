"""
Runs the full pipeline in order. Works the same on Windows, macOS
and Linux:

    pip install -r requirements.txt
    python run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Cleaning data", "clean_data.py"),
    ("Running EDA, KPIs and charts", "eda.py"),
    ("Running anomaly detection", "anomaly_detection.py"),
    ("Loading SQLite database and running SQL", "load_to_sqlite.py"),
    ("Building Tableau extract", "export_for_tableau.py"),
]

for i, (label, script) in enumerate(STEPS, start=1):
    print(f"\n[{i}/{len(STEPS)}] {label}...")
    subprocess.run([sys.executable, str(ROOT / "python" / script)], check=True)

print("\nDone. Outputs are in output/ and dashboard/.")
