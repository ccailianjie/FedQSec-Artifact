# FedQSec Artifact

This repository provides a compact reference implementation of the main
FedQSec workflow for the accompanying manuscript.

## Contents

- `src/fedqsec/`: selected executable modules for mode control, dynamic
  accumulator updates, federated Q-table updates, trust filtering, and workflow
  orchestration.
- `configs/`: parameters and experiment settings explicitly reported in the
  manuscript; unreported implementation settings are omitted.
- `examples/`: a lightweight runnable example of the public workflow.
- `results/reported/`: machine-readable CSV summaries aligned with the values
  reported in the manuscript tables.

## Environment

The reported experiments use the environment specified in the manuscript:

| Component | Environment |
| --- | --- |
| Operating system | Ubuntu 22.04 LTS |
| Python | 3.10 |
| Polynomial library | NTL 11.5.1 |
| Network simulation | SUMO 1.12 and Veins 5.3 |
| Blockchain simulation | OMNeT++ 6.0.3 and C++ |

The lightweight public example uses only the Python standard library and can
be run with Python 3.10:

```bash
python examples/demo.py
```

## Reproduction

The repository provides the core workflow, selected executable modules,
published experiment parameters, and reported result summaries to support
reproduction and inspection of the evaluation procedure described in the
manuscript.

## Datasets

The datasets are not redistributed in this repository. They can be obtained
from the following source repositories:

- [VeReMi position-falsification dataset](https://github.com/aektasharma/Veremi-dataset-classification.git)
- [NGSIM US-101 vehicle-trajectory dataset mirror](https://gitcode.com/open-source-toolkit/e3a10)

Please follow the access conditions and licensing terms provided by each source.

