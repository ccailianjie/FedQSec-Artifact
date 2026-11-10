#!/usr/bin/env python3
"""Aggregate the NTRU-GSC benchmark without embedding host-platform details."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OPERATIONS = ['KeyGen', 'Verify', 'Signature', 'Encryption', 'Signcrypt', 'Decrypt', 'Unsigncrypt']


def profiles():
    source = (HERE / 'bench.cpp').read_text()
    block = re.search(r'profiles\[\]\s*=\s*\{(.*?)\};', source, re.S).group(1)
    result = []
    for row in re.findall(r'\{([^{}]+)\}', block):
        i, d, m, q, sigma, sy, omega = row.split(',')
        result.append(dict(set=int(i), d=int(d), m=int(m), q=int(q),
                           sigma=float(sigma), sigma_y=float(sy), omega=int(omega)))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=REPO / 'results/crypto_benchmark')
    parser.add_argument('--export', type=Path, default=REPO / 'results/reported/crypto_runtime.csv')
    parser.add_argument('--samples', type=int, default=100)
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--warmup', type=int, default=20)
    parser.add_argument('--message-bytes', type=int, default=256)
    args = parser.parse_args()
    raw = list(csv.DictReader((args.input / 'run_raw.csv').open()))
    grouped, attempts = defaultdict(list), defaultdict(list)
    for row in raw:
        key = (int(row['set']), row['operation'], int(row['seed']))
        grouped[key].append(float(row['milliseconds']))
        if int(row['attempts']):
            attempts[key[:2]].append(int(row['attempts']))
    params = profiles()
    if len(raw) != len(params) * len(OPERATIONS) * args.samples * args.seeds:
        raise ValueError('Unexpected sample count; pass the actual sampling options.')
    summary = []
    for p in params:
        for op in OPERATIONS:
            groups = [v for (i, operation, _), v in grouped.items() if i == p['set'] and operation == op]
            if len(groups) != args.seeds or any(len(v) != args.samples for v in groups):
                raise ValueError('Incomplete operation/seed group')
            means = [statistics.mean(v) for v in groups]
            pooled = sorted(x for v in groups for x in v)
            aa = attempts.get((p['set'], op), [])
            summary.append(dict(set=p['set'], operation=op,
                                mean_ms=statistics.mean(means),
                                sd_seed_means_ms=statistics.stdev(means) if len(means) > 1 else 0,
                                median_ms=statistics.median(pooled),
                                p95_ms=pooled[math.ceil(.95 * len(pooled)) - 1],
                                minimum_ms=min(pooled), maximum_ms=max(pooled),
                                observations=len(pooled), seeds=len(groups),
                                mean_attempts=statistics.mean(aa) if aa else None,
                                empirical_acceptance=len(aa) / sum(aa) if aa else None))
    with (args.input / 'summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary)
    checks = [json.loads(s) for s in (args.input / 'run_checks.jsonl').read_text().splitlines()]
    if len(checks) != len(params) or any(c['status'] != 'passed' for c in checks):
        raise ValueError('Missing or failed correctness checks')
    metadata_file = args.input / 'measurement.json'
    metadata = json.loads(metadata_file.read_text()) if metadata_file.exists() else {}
    for name in ('operating_system', 'cpu', 'pinned_cpu', 'compiler', 'compiler_flags', 'openssl', 'origin'):
        metadata.pop(name, None)
    metadata.update(implementation='Four-response NTRU-GSC C++20 reference benchmark',
                    source_file='crypto/benchmark/bench.cpp',
                    source_sha256=hashlib.sha256((HERE / 'bench.cpp').read_bytes()).hexdigest(),
                    message_bytes=args.message_bytes, samples_per_seed=args.samples,
                    seed_count=args.seeds, warmup_per_seed=args.warmup,
                    seeds=sorted({int(row['seed']) for row in raw}),
                    dispersion='sample standard deviation of per-seed mean times; all observations retained',
                    ntt_profiles=params, checks=checks)
    metadata_file.write_text(json.dumps(metadata, indent=2) + '\n')
    lookup = {(r['set'], r['operation']): r for r in summary}
    columns = ['parameter_set', 'd', 'q', 'keygen_ms', 'verify_ms', 'signature_ms',
               'encryption_ms', 'signcrypt_ms', 'keygen_sd_ms', 'verify_sd_ms',
               'signature_sd_ms', 'encryption_sd_ms', 'signcrypt_sd_ms']
    args.export.parent.mkdir(parents=True, exist_ok=True)
    tex = []
    with args.export.open('w', newline='') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)
        for p in params:
            values = [lookup[p['set'], op] for op in OPERATIONS[:5]]
            name = ['I', 'II', 'III'][p['set'] - 1]
            writer.writerow([name, p['d'], p['q']] +
                            [f"{v['mean_ms']:.6f}" for v in values] +
                            [f"{v['sd_seed_means_ms']:.6f}" for v in values])
            tex.append('NTRU-GSC ' + name + ' & ' + ' & '.join(
                f"${v['mean_ms']:.3f} \\pm {v['sd_seed_means_ms']:.3f}$" for v in values) + r' \\')
            print(name + ': ' + ', '.join(f"{op}={v['mean_ms']:.3f} ms" for op, v in zip(OPERATIONS, values)))
    (args.input / 'table6_rows.tex').write_text('\n'.join(tex) + '\n')
    print(f'Updated {args.export}; retained {len(raw)} timing observations.')


if __name__ == '__main__':
    main()
