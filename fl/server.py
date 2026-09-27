"""RSU-side admission and regional Q-table aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from aggregators.aggregation import federated_average
from aggregators.trust import LocalUpdate, aggregation_weights, filter_by_credit
from datapreprocessor.data_utils import VehicleMessage
from .algorithms.fedql import QTable
from .client import Vehicle


@dataclass(frozen=True)
class RegionalUpdate:
    rsu_id: str
    table: QTable
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]


class RSU:
    def __init__(self, rsu_id: str) -> None:
        self.rsu_id = rsu_id
        self.vehicles: dict[str, Vehicle] = {}
        self.updates: list[LocalUpdate] = []

    def attach(self, vehicle: Vehicle) -> None:
        self.vehicles[vehicle.vehicle_id] = vehicle

    def receive(self, message: VehicleMessage, global_q: QTable) -> None:
        self.updates.append(self.vehicles[message.vehicle_id].local_update(message, global_q))

    def aggregate(self, global_q: QTable, threshold: float = 60.0) -> RegionalUpdate:
        accepted = filter_by_credit(self.updates, threshold)
        accepted_ids = {update.node_id for update in accepted}
        table = (federated_average([u.delta_q for u in accepted], aggregation_weights(accepted))
                 if accepted else dict(global_q))
        return RegionalUpdate(
            self.rsu_id,
            table,
            tuple(u.node_id for u in accepted),
            tuple(u.node_id for u in self.updates if u.node_id not in accepted_ids),
        )

    def distribute(self, table: QTable) -> None:
        for vehicle in self.vehicles.values():
            vehicle.receive_global(table)
        self.updates.clear()
