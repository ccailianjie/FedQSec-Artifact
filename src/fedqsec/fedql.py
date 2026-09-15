"""Selected tabular Q-learning and federated aggregation operations."""

from __future__ import annotations

import random
from collections.abc import Hashable, Sequence

State = Hashable
QTable = dict[tuple[State, int], float]


class TabularQAgent:
    def __init__(self, action_count: int, seed: int | None = None) -> None:
        if action_count <= 0:
            raise ValueError("action_count must be positive")
        self.action_count = action_count
        self.q: QTable = {}
        self.random = random.Random(seed)

    def value(self, state: State, action: int) -> float:
        return self.q.get((state, action), 0.0)

    def choose_action(self, state: State, epsilon: float) -> int:
        if not 0.0 <= epsilon <= 1.0:
            raise ValueError("epsilon must lie in [0, 1]")
        if self.random.random() < epsilon:
            return self.random.randrange(self.action_count)
        values = [self.value(state, action) for action in range(self.action_count)]
        return max(range(self.action_count), key=values.__getitem__)

    def update(
        self,
        state: State,
        action: int,
        reward: float,
        next_state: State,
        alpha: float,
        gamma: float,
    ) -> float:
        current = self.value(state, action)
        next_best = max(self.value(next_state, a) for a in range(self.action_count))
        updated = current + alpha * (reward + gamma * next_best - current)
        self.q[(state, action)] = updated
        return updated


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

