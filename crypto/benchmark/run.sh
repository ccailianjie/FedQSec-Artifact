#!/usr/bin/env bash
set -euo pipefail
benchmark_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(cd "$benchmark_dir/../.." && pwd)"
build_dir="$benchmark_dir/.build"
result_dir="${CRYPTO_BENCH_OUT:-$repo_dir/results/crypto_benchmark}"
mkdir -p "$build_dir" "$result_dir"
"${CXX:-g++}" -std=c++20 -O3 -DNDEBUG -march=native -Wall -Wextra -Wpedantic \
    "$benchmark_dir/bench.cpp" -lcrypto -o "$build_dir/benchmark"
samples="${BENCH_SAMPLES:-100}"
warmup="${BENCH_WARMUP:-20}"
seeds="${BENCH_SEEDS:-10}"
message_bytes="${BENCH_MESSAGE_BYTES:-256}"
checks="${BENCH_SELFTEST_CASES:-100}"
command_args=("$build_dir/benchmark" --samples "$samples" --warmup "$warmup" \
    --seeds "$seeds" --selftest-cases "$checks" --message-bytes "$message_bytes" --out "$result_dir/run")
if [[ -n "${BENCH_CPU:-}" ]]; then
    taskset -c "$BENCH_CPU" "${command_args[@]}"
else
    "${command_args[@]}"
fi
python3 "$benchmark_dir/summarize.py" --input "$result_dir" \
    --export "${CRYPTO_BENCH_CSV:-$repo_dir/results/reported/crypto_runtime.csv}" \
    --samples "$samples" --seeds "$seeds" --warmup "$warmup" --message-bytes "$message_bytes"
