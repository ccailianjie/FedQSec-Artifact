#!/usr/bin/env bash
set -eu

cd "$(dirname "$0")/.."
python3 examples/demo.py
python3 batchrun.py
python3 blockchain/pbft_study.py
python3 scripts/inspect_reported.py
