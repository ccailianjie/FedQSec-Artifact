"""Weighted regional and cloud Q-table aggregation."""

from __future__ import annotations

from collections.abc import Sequence

from fl.algorithms.fedql import QTable


def federated_average(tables: Sequence[QTable], weights: Sequence[float]) -> QTable:
    if not tables or len(tables) != len(weights):
        raise ValueError("tables and weights must have the same non-zero length")
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("weights must be non-negative with a positive sum")
    keys = set().union(*(table.keys() for table in tables))
    total_weight = sum(weights)
    return {
        key: sum(weight * table.get(key, 0.0) for table, weight in zip(tables, weights))
        / total_weight
        for key in keys
    }
