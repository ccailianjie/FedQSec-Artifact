# FedQSec Artifact

This repository provides a compact, executable artifact for the FedQSec
framework described in the accompanying manuscript. It exposes the system
workflow, selected framework modules, manuscript-reported configurations, and
machine-readable summaries of the reported results while omitting private
research implementation details.

## Repository Contents

- `src/fedqsec/`: selected modules for tabular Q-learning, hierarchical
  aggregation, credit-assisted filtering, mode control, dynamic accumulator
  updates, and workflow orchestration.
- `examples/demo.py`: a standard-library-only executable demonstration of the
  end-to-end FedQSec data flow.
- `configs/`: parameters and experimental settings explicitly reported in the
  manuscript. Unreported implementation parameters are intentionally omitted.
- `results/reported/`: CSV summaries corresponding to Tables 4, 5, and 7-12 of
  the manuscript.
- `docs/reproducibility.md`: environment, execution, and artifact-to-paper
  mapping.

## Lightweight End-to-End Workflow

The runnable example connects the main architectural stages:

1. vehicle messages and context observations are collected by OBUs;
2. each OBU encodes an 81-state context and performs reduced local tabular
   Q-learning updates over nine security actions;
3. RSUs apply credit-assisted admission and regional Q-table aggregation;
4. the cloud aggregates regional tables and redistributes the global policy;
5. the selected action determines the NTRU-GSC mode and parameter set;
6. the protected packet updates the dynamic accumulator; and
7. an audit record passes through a reduced PBFT commit interface.

## Environment

The manuscript reports the following experimental environment:

| Component | Reported environment |
| --- | --- |
| Operating system | Ubuntu 22.04 LTS |
| GPU | 2 NVIDIA GeForce RTX 4090 D GPUs (48 GB VRAM) |
| CPU | 10-core CPU |
| Memory | 56 GB DDR4 |
| Languages | C++ and Python 3.10 |
| Polynomial library | NTL 11.5.1 |
| Network simulation | SUMO 1.12 and Veins 5.3 |
| Blockchain simulation | C++ and OMNeT++ 6.0.3|

## Quick Start

Python 3.10 or later is sufficient for the lightweight workflow:

```bash
python examples/demo.py
```

Expected completion message:

```text
Workflow completed successfully.
```

No dataset download, model weight, GPU, SUMO, Veins, NTL, or OMNeT++
installation is required for this reduced example.

## Paper-to-Artifact Mapping

| Manuscript component | Public artifact |
| --- | --- |
| NTRU-GSC parameter sets and modes | `configs/ntru_parameters.yaml`, `src/fedqsec/modes.py` |
| Dynamic accumulator workflow | `src/fedqsec/accumulator.py` |
| 81-state, 9-action FedQL model | `configs/fedql.yaml`, `src/fedqsec/fedql.py` |
| Cloud-fog-vehicle orchestration | `src/fedqsec/framework.py`, `examples/demo.py` |
| Credit-assisted update filtering | `src/fedqsec/trust.py`, `examples/demo.py` |
| SUMO/Veins settings | `configs/network.yaml` |
| PBFT and storage settings | `configs/blockchain.yaml` |
| Manuscript table values | `results/reported/` |

## Datasets

Datasets are not redistributed in this repository. The manuscript uses the
following public sources:

- [VeReMi position-falsification dataset](https://github.com/aektasharma/Veremi-dataset-classification.git)
- [NGSIM US-101 vehicle-trajectory dataset mirror](https://gitcode.com/open-source-toolkit/e3a10)

Please follow the access conditions and licensing terms provided by each
source.

## License

This artifact is released under the [MIT License](LICENSE).
