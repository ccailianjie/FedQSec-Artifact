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
| Poisoning case | Reward reversal input for a small local update ([`attackers/`](attackers/)) |
| Data processing | Vehicle context encoding ([`datapreprocessor/`](datapreprocessor/)) |
| Cryptography | Ring operations, mode selection, protection interface, and accumulator ([`crypto/`](crypto/)) |
| Blockchain | Audit receipt and PBFT round accounting ([`blockchain/`](blockchain/)) |

## Federated Q-Learning Components

| Component | Source File | Role |
| --- | --- | --- |
| Tabular Q-learning | [`fl/algorithms/fedql.py`](fl/algorithms/fedql.py) | Action choice and temporal-difference update |
| Local training | [`fl/local_training.py`](fl/local_training.py) | Local transitions and exploration schedule |
| Vehicle | [`fl/client.py`](fl/client.py) | Prepares local Q-table updates |
| RSU | [`fl/server.py`](fl/server.py) | Filters updates and forms a regional table |
| Cloud | [`fl/coordinator.py`](fl/coordinator.py) | Combines regional tables and selects an action |
| Round workflow | [`fl/workflow.py`](fl/workflow.py) | Connects vehicles, RSUs, cloud, protection, and audit |

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

## Getting Started

Run the connected example and two small component cases with Python 3.10:

```bash
python main.py
python batchrun.py
python blockchain/pbft_study.py
```

`main.py` sends six vehicle observations to two RSUs, filters a low-credit
update, combines regional Q-tables, selects a security action, and records an
audit receipt. Its message branches use hash-based adapters.

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

## Code Availability

The complete source code and full implementation will be further uploaded
after manuscript acceptance.

## License

The repository is provided under the [MIT License](LICENSE).
