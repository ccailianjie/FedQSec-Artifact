# Reproducibility Guide

## 1. Lightweight Workflow

The public workflow is designed for Python 3.10 and uses only the standard
library:

```bash
bash scripts/run_artifact.sh
```

Individual entry points:

```bash
python main.py
python examples/demo.py
python batchrun.py
python blockchain/pbft_study.py
python scripts/inspect_reported.py
```

The detailed example executes a connected path from vehicle observations to
local Q-table updates, RSU filtering and regional aggregation, cloud
aggregation, adaptive security selection, dynamic accumulator update, and a
PBFT commit receipt. `environment.yml` provides a Python 3.10 Conda
environment for these commands.
The workflow reads six fixed synthetic messages from
`data/sample_vehicle_messages.csv`; the manuscript evaluation seed list is
stored separately in `configs/seeds.txt`.

## 2. Manuscript Environment

The manuscript reports Ubuntu 22.04 LTS, two NVIDIA GeForce RTX 4090 D GPUs
(48 GB VRAM), a 10-core CPU, 56 GB DDR4 memory, Python 3.10, C++, NTL 11.5.1,
SUMO 1.12, and Veins 5.3. PBFT is implemented in C++ on the OMNeT++ platform.
The public artifact configuration records OMNeT++ 6.0.3 as the implementation
version.

The Veins network configuration is in `network_simulation/`. PBFT phase logic,
transaction messages, and the network topology are in `blockchain/simulation/`.

## 3. Reported Evaluation Settings

- NTRU-GSC: three parameter sets and three modes, giving nine actions.
- FedQL: 81 context states, 20 vehicle agents, four fog nodes, one cloud
  coordinator, and 100 local updates per communication round.
- Hyperparameter study: 1000 rounds and 10 independent seeds.
- Poisoning study: 300 rounds, 10 seeds, and malicious-agent ratios of 10%,
  20%, and 30%.
- Network simulation: IEEE 802.11p, 1 s safety beacons, and 600 s runs.
- Blockchain simulation: 20 cloud full nodes and 5 ms inter-node propagation.

Exact values are stored under `configs/`. The ten reported random seeds are in
`configs/seeds.txt`.

## 4. Result Inspection

The files in `results/reported/` mirror manuscript table values:

| CSV file | Manuscript table |
| --- | --- |
| `basic_operations.csv` | Table 4 |
| `crypto_runtime.csv` | Table 5 |
| `batch_verification.csv` | Table 7 |
| `hyperparameter_sensitivity.csv` | Table 8 |
| `ablation.csv` | Table 9 |
| `poisoning_robustness.csv` | Table 10 |
| `fedql_comparison.csv` | Table 11 |
| `blockchain_overhead.csv` | Table 12 |

Run `python scripts/inspect_reported.py` to inspect CSV columns and row counts.

## 5. Datasets

- VeReMi: <https://github.com/aektasharma/Veremi-dataset-classification.git>
- NGSIM US-101 mirror: <https://gitcode.com/open-source-toolkit/e3a10>

The repository does not redistribute either dataset.
