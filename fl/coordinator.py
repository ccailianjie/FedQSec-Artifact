"""Cloud-side aggregation and global security-action selection."""

from __future__ import annotations

from aggregators.aggregation import federated_average
from crypto.modes import CryptoMode, SecurityAction
from datapreprocessor.data_utils import ContextState, state_index
from .algorithms.fedql import QTable
from .server import RegionalUpdate

MODES = (CryptoMode.SIGNATURE, CryptoMode.ENCRYPTION, CryptoMode.SIGNCRYPTION)
PROFILES = ("I", "II", "III")
ACTIONS = tuple(SecurityAction(profile, mode) for mode in MODES for profile in PROFILES)


class Cloud:
    def __init__(self) -> None:
        self.q: QTable = {}
        self.version = 0

    def aggregate(self, regions: list[RegionalUpdate]) -> QTable:
        self.q = federated_average([region.table for region in regions], [1.0] * len(regions))
        self.version += 1
        return self.q

    def select(self, state: ContextState) -> SecurityAction:
        index = state_index(state)
        action_id = max(range(len(ACTIONS)), key=lambda a: self.q.get((index, a), 0.0))
        return ACTIONS[action_id]
