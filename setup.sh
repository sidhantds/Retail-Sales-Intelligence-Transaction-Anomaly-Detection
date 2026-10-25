#!/usr/bin/env bash
# Installs dependencies and rebuilds the full pipeline.
# On Windows, run the two commands below directly instead.
set -e

cd "$(dirname "$0")"

pip install -q -r requirements.txt
python run_pipeline.py
