"""Vehicle-side local FedQL update and global table reception."""

from __future__ import annotations

from aggregators.trust import LocalUpdate
from datapreprocessor.data_utils import VehicleMessage, encode_context, state_index
from .algorithms.fedql import QTable, TabularQAgent
from .local_training import local_q_updates


def action_for_example(message: VehicleMessage) -> int:
    priority = encode_context(message).priority
    if priority == 3:
        return 5
    if priority == 2:
        return 4
    return 0


class Vehicle:
    def __init__(self, vehicle_id: str, seed: int) -> None:
        self.vehicle_id = vehicle_id
        self.agent = TabularQAgent(action_count=9, seed=seed)

    def local_update(self, message: VehicleMessage, global_q: QTable) -> LocalUpdate:
        self.agent.q = dict(global_q)
        state = state_index(encode_context(message))
        action = action_for_example(message)
        local_table = local_q_updates(self.agent, [(state, action, 1.0, state)])
        return LocalUpdate(self.vehicle_id, message.credit, 1, local_table)

    def receive_global(self, table: QTable) -> None:
        self.agent.q = dict(table)
