# Welcome to FedQSec

![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-MIT-green)

FedQSec combines federated Q-learning, adaptive NTRU-GSC modes, credit-based
update filtering, a dynamic accumulator, and blockchain auditing for IoV
security. This repository provides the framework components, reported settings,
and table summaries associated with the manuscript.

## Features

| Category | Details |
| --- | --- |
| Federated learning | Vehicle, RSU, and cloud roles with an 81-state, nine-action Q-table ([`fl/`](fl/)) |
| Aggregation | Credit filtering and weighted regional aggregation ([`aggregators/`](aggregators/)) |
| Poisoning case | Reward reversal inputs for local updates ([`attackers/`](attackers/)) |
| Data processing | Vehicle context encoding ([`datapreprocessor/`](datapreprocessor/)) |
| Cryptography | Ring operations, mode selection, protection interface, and accumulator ([`crypto/`](crypto/)) |
| Blockchain | Audit receipts, PBFT phase handling, and network relay ([`blockchain/`](blockchain/)) |
| Network simulation | Veins scenario and IEEE 802.11p settings ([`network_simulation/`](network_simulation/)) |

## Project Structure

```text
FedQSec-Artifact/
├── fl/                  # Vehicle, RSU, cloud, and FedQL components
├── aggregators/         # Regional aggregation and credit admission
├── attackers/           # Reward-reversal input
├── datapreprocessor/    # Vehicle context encoding
├── crypto/              # Ring helpers, mode interface, accumulator
├── blockchain/          # PBFT phases, topology, and audit receipt
├── network_simulation/  # Veins scenario and radio configuration
├── configs/             # Manuscript-reported settings and seeds
├── data/                # Vehicle-message inputs for the example
├── examples/            # Detailed executable architecture example
├── scripts/             # One-command run and reported-CSV inspection
├── results/reported/    # Manuscript table summaries
├── docs/                # Environment and paper-to-artifact mapping
├── main.py              # Modular workflow entry point
└── batchrun.py          # Regular/reward-reversal comparison
```

## Federated Q-Learning Components

| Component | Source File | Role |
| --- | --- | --- |
| Tabular Q-learning | [`fl/algorithms/fedql.py`](fl/algorithms/fedql.py) | Action choice and temporal-difference update |
| Local training | [`fl/local_training.py`](fl/local_training.py) | Local transitions and exploration schedule |
| Vehicle | [`fl/client.py`](fl/client.py) | Prepares local Q-table updates |
| RSU | [`fl/server.py`](fl/server.py) | Filters updates and forms a regional table |
| Cloud | [`fl/coordinator.py`](fl/coordinator.py) | Combines regional tables and selects an action |
| Round workflow | [`fl/workflow.py`](fl/workflow.py) | Connects vehicles, RSUs, cloud, protection, and audit |
| Detailed data-flow example | [`examples/demo.py`](examples/demo.py) | Runs the vehicle–RSU–cloud–crypto–audit sequence with explicit classes and trace output |

## Security and Audit Components

| Component | Source File | Role |
| --- | --- | --- |
| Credit filter | [`aggregators/trust.py`](aggregators/trust.py) | Admits updates above the reported credit threshold |
| Aggregation | [`aggregators/aggregation.py`](aggregators/aggregation.py) | Computes weighted Q-table averages |
| Reward reversal | [`attackers/reward_reversal.py`](attackers/reward_reversal.py) | Changes a local reward sign |
| NTRU ring helpers | [`crypto/polynomial.py`](crypto/polynomial.py) | Coefficient sampling, norm check, and ring multiplication |
| Protection branches | [`crypto/modes.py`](crypto/modes.py), [`crypto/crypto_core.py`](crypto/crypto_core.py) | Dispatches signature, encryption, and signcryption modes |
| Accumulator | [`crypto/accumulator.py`](crypto/accumulator.py) | Updates a message-linked digest state |
| PBFT accounting | [`blockchain/audit.py`](blockchain/audit.py), [`blockchain/pbft_study.py`](blockchain/pbft_study.py) | Generates an audit receipt and round estimates |
| PBFT simulation components | [`blockchain/simulation/`](blockchain/simulation/) | Includes phase vote tracking, transaction messages, relay timing, and the cloud topology |

## Quick Start

Use Python 3.10. A Conda environment is provided in
[`environment.yml`](environment.yml). From the repository root:

```bash
bash scripts/run_artifact.sh
```

The script runs the data-flow example, a reward-reversal case,
PBFT round accounting, and inspection of the included reported CSV summaries.
Both workflow entry points read the same fixed synthetic input file in
[`data/`](data/); component random generators use fixed seeds. Manuscript
evaluation seeds are listed in [`configs/seeds.txt`](configs/seeds.txt).
The commands can also be run separately:

```bash
python main.py
python examples/demo.py
python batchrun.py
python blockchain/pbft_study.py
python scripts/inspect_reported.py
```

`main.py` uses the package modules. `examples/demo.py` retains the longer
connected example with state encoding, local updates, RSU filtering, cloud
distribution, mode selection, accumulator updates, and a PBFT receipt.

| Manuscript item | Public file | Command or inspection |
| --- | --- | --- |
| FedQL state/action flow | [`fl/`](fl/), [`examples/demo.py`](examples/demo.py) | `python examples/demo.py` |
| Credit filtering and reward reversal | [`aggregators/`](aggregators/), [`attackers/`](attackers/) | `python batchrun.py` |
| PBFT quorum accounting | [`blockchain/`](blockchain/) | `python blockchain/pbft_study.py` |
| Tables 4, 5, 7–12 | [`results/reported/`](results/reported/) | `python scripts/inspect_reported.py` |

## Experiment Environment

| Component | Manuscript environment |
| --- | --- |
| Operating system | Ubuntu 22.04 LTS |
| GPU | 2 NVIDIA GeForce RTX 4090 D GPUs (48 GB VRAM) |
| CPU and memory | 10-core CPU; 56 GB DDR4 |
| Languages | C++ and Python 3.10 |
| Polynomial library | NTL 11.5.1 |
| Network simulation | SUMO 1.12; Veins 5.3 |
| Blockchain simulation | C++ on OMNeT++ 6.0.3 |

The runnable example uses in-memory messages. The reported experiment
parameters are in [`configs/`](configs/), with the software environment in
[`environment.yaml`](environment.yaml). The ten reported seeds are in
[`configs/seeds.txt`](configs/seeds.txt).

## Results and Datasets

[`results/reported/`](results/reported/) contains CSV summaries for manuscript
Tables 4, 5, and 7–12. The data sources are:

- [VeReMi position-falsification dataset](https://github.com/aektasharma/Veremi-dataset-classification.git)
- [NGSIM US-101 vehicle-trajectory dataset mirror](https://gitcode.com/open-source-toolkit/e3a10)

See [`docs/reproducibility.md`](docs/reproducibility.md) for the environment,
settings, and manuscript table mapping.

## License

The project-authored files are provided under the [MIT License](LICENSE).
