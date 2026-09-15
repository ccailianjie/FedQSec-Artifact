"""Credit-assisted filtering used before regional Q-table aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from .fedql import QTable


@dataclass(frozen=True)
class LocalUpdate:
    node_id: str
    credit: float
    sample_count: int
    delta_q: QTable


def filter_by_credit(updates: list[LocalUpdate], minimum_credit: float) -> list[LocalUpdate]:
    return [
        update
        for update in updates
        if update.credit >= minimum_credit and update.sample_count > 0
    ]


def aggregation_weights(updates: list[LocalUpdate]) -> list[float]:
    return [update.credit * update.sample_count for update in updates]

