# Experiment Configurations

These files collect only parameters stated in the manuscript or explicitly
identified as public artifact metadata. Unreported training and implementation
settings are omitted.

- `ntru_parameters.yaml`: the three NTRU-GSC parameter sets in Table 3.
- `fedql.yaml`: the reported state/action design, federation topology, training
  parameters, dataset counts, and poisoning settings.
- `network.yaml`: the reported SUMO/Veins communication setup.
- `blockchain.yaml`: the reported PBFT and storage settings in Table 12.
- `../environment.yaml`: the hardware and software environment in Section 7.1;
  OMNeT++ 6.0.3 is recorded as public artifact metadata.
- `seeds.txt`: the ten independent random seeds used in randomized tests.
