# NTRU-GSC cryptographic performance benchmark

This executable implements the current four-response construction and generates
the cryptographic runtime CSV. It is separate from the lightweight Python
architecture demonstration.

## Parameters

| Set | d | m | q | sigma | sigma_y | omega | Ring polynomial |
|---|---:|---:|---:|---:|---:|---:|---|
| I | 1024 | 2048 | 2101249 | 1.1 | 19114 | 16 | X^1024+1 |
| II | 1536 | 4608 | 10418689 | 1.5 | 77484 | 24 | X^1536-X^768+1 |
| III | 2048 | 4096 | 14012417 | 1.9 | 90462 | 31 | X^2048+1 |

The executable contains its parameter profiles in `bench.cpp`, matching
`configs/ntru_parameters.yaml`; the result metadata records these profiles.

## Run

Dependencies: a C++20 compiler, OpenSSL development headers/libraries with
SHAKE256, and Python 3. From the repository root:

```bash
bash scripts/benchmark_crypto.sh
```

The command compiles the executable, performs correctness checks, records raw
timings, and refreshes `results/reported/crypto_runtime.csv`. It does not run or
modify the federated-learning, network, or blockchain experiments.

The default is 256-byte messages, 10 seeds, 20 warm-up calls and 100 measured
calls per operation and seed. For a short check without overwriting the
published measurement files:

```bash
CRYPTO_BENCH_OUT=/tmp/fedqsec-crypto-smoke \
CRYPTO_BENCH_CSV=/tmp/fedqsec-crypto-smoke.csv \
BENCH_SAMPLES=3 BENCH_WARMUP=1 BENCH_SEEDS=1 BENCH_SELFTEST_CASES=3 \
bash scripts/benchmark_crypto.sh
```

`BENCH_MESSAGE_BYTES`, `BENCH_CPU` (optional affinity), and `CXX` can also be
set when running the benchmark.

## Implementation and timing scope

- Dense products use NTT with the actual cyclotomic polynomial; Set II uses
  mixed radix-2/3. Sparse ternary challenge products use sparse convolution.
- User and partial secrets are sampled with both the coefficient and L2 bounds.
  Partial keys use small-secret sampling; user authentication uses independent
  `a_sig` and four response polynomials.
- Joint rejection sampling uses M=exp(1+1/144), with every failed attempt included
  in generation time. The final response satisfies the coefficient bound.
- SHAKE256 implements purpose-separated, length-delimited hash inputs. The
  reconciliation formulas use the selected q rather than constants for 12289.
- The Gaussian sampler is a finite-precision inverse-CDF reference sampler.
  This implementation does not include side-channel hardening.
- System initialization, Gaussian lookup tables and reusable NTT precomputation
  are outside per-operation timing. KeyGen measures one vehicle in one set,
  including the user/partial/KEM keys, pseudonym and partial-key validation.
- Verify means signature verification with norm, challenge and accumulator-update
  checks. Decrypt and Unsigncrypt are recorded separately.
- Serialization uses little-endian int32 polynomials and 2-bit reconciliation
  values. Payload size records are not ideal bit-packing estimates.
- Network, blockchain, persistent replay-log I/O and HMAC sessions are outside
  this cryptographic benchmark.

## Results

`results/crypto_benchmark/` contains raw per-operation timings, correctness
checks, payload sizes, summary statistics, measurement settings and LaTeX rows.
The runtime CSV preserves its original mean column names and appends five
standard-deviation columns. SD is the sample standard deviation of the ten
seed-wise mean times; no slow observations are removed.

Correctness checks compare NTT products to schoolbook products, check the NTRU
key relation and the actual ring reduction, exercise all three modes, and reject
modified authenticated messages/counters, oversized responses and modified
signcryptions. Every generated benchmark message is verified or recovered.

Reconciliation algorithm reference:
https://github.com/tpoeppelmann/newhope/blob/master/ref/error_correction.c
