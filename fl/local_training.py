"""Local Q-learning updates for a federated workflow."""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from typing import Protocol

from .algorithms.fedql import QTable, TabularQAgent

Transition = tuple[Hashable, int, float, Hashable]


class LocalEnvironment(Protocol):
    def reset(self) -> Hashable: ...

    def step(self, action: int) -> tuple[Hashable, float, bool]: ...


def epsilon_at_step(step: int, start: float = 0.9, decay: float = 0.001) -> float:
    """Linear exploration schedule reported in the manuscript."""
    if step < 0:
        raise ValueError("step must be nonnegative")
    return max(0.0, start - decay * step)


def local_q_updates(
    agent: TabularQAgent,
    transitions: Iterable[Transition],
    *,
    alpha: float = 0.1,
    gamma: float = 0.9,
) -> QTable:
    """Apply observed transitions and return a local table for RSU upload."""
    for state, action, reward, next_state in transitions:
        agent.update(state, action, reward, next_state, alpha, gamma)
    return dict(agent.q)


def train_local_episode(
    agent: TabularQAgent,
    environment: LocalEnvironment,
    *,
    steps: int,
    epsilon: float,
    alpha: float = 0.1,
    gamma: float = 0.9,
) -> QTable:
    """Act, observe, and update the local Q-table."""
    state = environment.reset()
    for _ in range(steps):
        action = agent.choose_action(state, epsilon)
        next_state, reward, done = environment.step(action)
        agent.update(state, action, reward, next_state, alpha, gamma)
        state = next_state
        if done:
            break
    return dict(agent.q)
