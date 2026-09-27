"""PBFT round-level quorum and message accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoundEstimate:
    replicas: int
    faulty_replicas: int
    tolerates_faults: bool
    quorum: int
    prepare_messages: int
    commit_messages: int


def estimate_round(replicas: int, faulty_replicas: int) -> RoundEstimate:
    """Calculate the 3f+1 tolerance and quadratic vote exchanges."""
    if replicas < 1 or not 0 <= faulty_replicas < replicas:
        raise ValueError("invalid replica or fault count")
    quorum = 2 * ((replicas - 1) // 3) + 1
    exchanges = replicas * (replicas - 1)
    return RoundEstimate(
        replicas,
        faulty_replicas,
        replicas >= 3 * faulty_replicas + 1,
        quorum,
        exchanges,
        exchanges,
    )


if __name__ == "__main__":
    for size in (4, 7, 10):
        print(estimate_round(size, faulty_replicas=1))
